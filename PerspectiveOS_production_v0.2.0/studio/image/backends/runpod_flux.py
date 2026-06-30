"""RunPod ComfyUI (FLUX.1-dev) backend.

Talks to a RunPod Serverless endpoint running ``runpod/worker-comfyui:*-flux1-dev``.
The request body is ``{"input": {"workflow": <ComfyUI API graph>}}`` and the worker
returns base64 PNG(s). Model files baked into that image:
``flux1-dev.safetensors`` (fp8), ``t5xxl_fp8_e4m3fn`` + ``clip_l``, VAE ``ae.safetensors``.

Phase 2: text-to-image only. ``reference_paths`` are accepted but NOT yet used —
reference conditioning (a persona LoRA, or Flux Redux/Kontext) is Phase 3 and needs
extra models/nodes that are not in the stock worker image.
"""
import base64
import json
import random
import time
import urllib.error
import urllib.request
from pathlib import Path

try:
    from .base import ImageBackend, ImageGenerationError
except ImportError:
    from image.backends.base import ImageBackend, ImageGenerationError

_HEADERS_UA = "Mozilla/5.0"


class RunPodFluxBackend(ImageBackend):
    name = "runpod_flux"

    def __init__(
        self,
        api_key: str,
        endpoint: str,
        *,
        steps: int = 20,
        guidance: float = 3.5,
        poll_interval: float = 5.0,
        max_polls: int = 60,
        timeout: float = 300.0,
    ) -> None:
        if not api_key or not endpoint:
            raise ImageGenerationError(
                "RunPod Flux backend needs RUNPOD_API_KEY and RUNPOD_FLUX_ENDPOINT."
            )
        endpoint = endpoint.rstrip("/")
        if "://" not in endpoint:
            endpoint = "https://" + endpoint
        self.endpoint = endpoint
        self.api_key = api_key
        self.steps = steps
        self.guidance = guidance
        self.poll_interval = poll_interval
        self.max_polls = max_polls
        self.timeout = timeout

    # ----- public API -----------------------------------------------------
    def generate(self, *, prompt: str, reference_paths: list[Path], size: str) -> bytes:
        if reference_paths:
            # Phase 2: the stock flux1-dev worker is text-to-image only. References are
            # honoured as descriptive text in the prompt, not attached as images yet.
            print(
                f"[runpod_flux] note: {len(reference_paths)} reference image(s) ignored "
                "(text-to-image; reference conditioning is Phase 3)."
            )
        width, height = self._parse_size(size)
        workflow = self._build_workflow(prompt, width, height, random.randint(1, 2**31 - 1))
        return self._run(workflow)

    # ----- internals ------------------------------------------------------
    @staticmethod
    def _parse_size(size: str) -> tuple[int, int]:
        try:
            w, h = (int(v) for v in size.lower().split("x"))
        except Exception:
            w, h = 1024, 1536
        # Flux wants multiples of 16.
        return (w // 16) * 16, (h // 16) * 16

    def _build_workflow(self, prompt: str, width: int, height: int, seed: int) -> dict:
        return {
            "5": {"class_type": "EmptyLatentImage",
                  "inputs": {"width": width, "height": height, "batch_size": 1}},
            "6": {"class_type": "CLIPTextEncode",
                  "inputs": {"text": prompt, "clip": ["11", 0]}},
            "26": {"class_type": "FluxGuidance",
                   "inputs": {"guidance": self.guidance, "conditioning": ["6", 0]}},
            "8": {"class_type": "VAEDecode",
                  "inputs": {"samples": ["13", 0], "vae": ["10", 0]}},
            "9": {"class_type": "SaveImage",
                  "inputs": {"filename_prefix": "perspective_flux", "images": ["8", 0]}},
            "10": {"class_type": "VAELoader", "inputs": {"vae_name": "ae.safetensors"}},
            "11": {"class_type": "DualCLIPLoader",
                   "inputs": {"clip_name1": "t5xxl_fp8_e4m3fn.safetensors",
                              "clip_name2": "clip_l.safetensors", "type": "flux"}},
            "12": {"class_type": "UNETLoader",
                   "inputs": {"unet_name": "flux1-dev.safetensors", "weight_dtype": "fp8_e4m3fn"}},
            "13": {"class_type": "SamplerCustomAdvanced",
                   "inputs": {"noise": ["25", 0], "guider": ["22", 0], "sampler": ["16", 0],
                              "sigmas": ["17", 0], "latent_image": ["5", 0]}},
            "16": {"class_type": "KSamplerSelect", "inputs": {"sampler_name": "euler"}},
            "17": {"class_type": "BasicScheduler",
                   "inputs": {"scheduler": "sgm_uniform", "steps": self.steps, "denoise": 1,
                              "model": ["12", 0]}},
            "22": {"class_type": "BasicGuider",
                   "inputs": {"model": ["12", 0], "conditioning": ["26", 0]}},
            "25": {"class_type": "RandomNoise", "inputs": {"noise_seed": seed}},
        }

    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json", "User-Agent": _HEADERS_UA}

    def _call(self, url: str, data: dict | None = None, method: str = "GET") -> tuple[object, str]:
        req = urllib.request.Request(
            url, headers=self._headers(), method=method,
            data=json.dumps(data).encode() if data else None,
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                return resp.status, resp.read().decode()
        except urllib.error.HTTPError as exc:
            return exc.code, exc.read().decode()

    def _run(self, workflow: dict) -> bytes:
        status, body = self._call(self.endpoint + "/runsync", {"input": {"workflow": workflow}}, "POST")
        try:
            job = json.loads(body)
        except json.JSONDecodeError as exc:
            raise ImageGenerationError(f"RunPod returned non-JSON (HTTP {status}): {body[:200]}") from exc

        job_id, state = job.get("id"), job.get("status")
        polls = 0
        while state in ("IN_QUEUE", "IN_PROGRESS") and job_id and polls < self.max_polls:
            time.sleep(self.poll_interval)
            polls += 1
            _, poll_body = self._call(self.endpoint + f"/status/{job_id}")
            job = json.loads(poll_body)
            state = job.get("status")

        if state != "COMPLETED":
            detail = job.get("error") or json.dumps(job)[:300]
            raise ImageGenerationError(f"RunPod Flux generation did not complete (status {state}): {detail}")

        images = (job.get("output") or {}).get("images") or []
        if not images:
            raise ImageGenerationError(f"RunPod Flux returned no images: {json.dumps(job.get('output'))[:300]}")
        data = images[0].get("data") or images[0].get("image")
        if not data:
            raise ImageGenerationError(
                "RunPod Flux returned an image reference without base64 data (S3 mode not supported): "
                f"{json.dumps(images[0])[:300]}"
            )
        return base64.b64decode(data)
