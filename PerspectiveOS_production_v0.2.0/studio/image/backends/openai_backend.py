"""OpenAI gpt-image-1 backend — preserves the existing generation behaviour.

No references  -> ``images.generate`` (text-to-image).
With references -> ``images.edit`` with the reference handles, including the
nondeterministic-output-moderation retry that discreet scenes need.
"""
import base64
from pathlib import Path

try:
    from .base import ImageBackend, ImageGenerationError
except ImportError:
    from image.backends.base import ImageBackend, ImageGenerationError


class OpenAIImageBackend(ImageBackend):
    name = "openai"

    def __init__(self, api_key: str, model: str = "gpt-image-1") -> None:
        if not api_key:
            raise ImageGenerationError(
                "No OpenAI API key provided. Set OPENAI_API_KEY or enter a key in the sidebar."
            )
        self.api_key = api_key
        self.model = model

    def generate(self, *, prompt: str, reference_paths: list[Path], size: str) -> bytes:
        try:
            from openai import OpenAI
        except ImportError as exc:  # pragma: no cover - dependency hint
            raise ImageGenerationError(
                "The 'openai' package is not installed. Run: pip install -r requirements.txt"
            ) from exc

        client = OpenAI(api_key=self.api_key)

        if not reference_paths:
            try:
                result = client.images.generate(
                    model=self.model, prompt=prompt, size=size, quality="high", n=1
                )
            except Exception as exc:  # surface API/auth/quota errors
                raise ImageGenerationError(f"Image generation failed: {exc}") from exc
            return base64.b64decode(result.data[0].b64_json)

        # gpt-image-1 output moderation is nondeterministic - a discreet scene that trips the
        # "sexual" classifier on one draw often passes on the next, so retry a few times before
        # surfacing the block. Other errors (billing, auth) are not retried.
        max_attempts = 3
        for attempt in range(1, max_attempts + 1):
            handles = [path.open("rb") for path in reference_paths]
            try:
                result = client.images.edit(
                    model=self.model, image=handles, prompt=prompt, size=size, quality="high", n=1
                )
                return base64.b64decode(result.data[0].b64_json)
            except TypeError as exc:
                raise ImageGenerationError(
                    "Reference-guided image generation is not supported by the installed OpenAI SDK. "
                    "Update dependencies with: pip install -r requirements.txt"
                ) from exc
            except Exception as exc:
                message = str(exc)
                is_moderation = "moderation_blocked" in message or "safety system" in message
                if is_moderation and attempt < max_attempts:
                    continue
                raise ImageGenerationError(
                    f"Reference-guided image generation failed: {exc}"
                ) from exc
            finally:
                for handle in handles:
                    handle.close()
        # Unreachable: the loop either returns or raises.
        raise ImageGenerationError("Image generation failed after retries.")
