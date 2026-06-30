"""Image-backend registry.

``get_backend("openai" | "runpod_flux")`` returns a ready ``ImageBackend``. RunPod
credentials are read from the environment (``RUNPOD_API_KEY`` / ``RUNPOD_FLUX_ENDPOINT``);
the OpenAI key is passed in (it is the same key GPT uses for prompts/review).
"""
import os

try:
    from .base import ImageBackend, ImageGenerationError
    from .openai_backend import OpenAIImageBackend
    from .runpod_flux import RunPodFluxBackend
except ImportError:
    from image.backends.base import ImageBackend, ImageGenerationError
    from image.backends.openai_backend import OpenAIImageBackend
    from image.backends.runpod_flux import RunPodFluxBackend

__all__ = ["ImageBackend", "ImageGenerationError", "OpenAIImageBackend",
           "RunPodFluxBackend", "get_backend"]

_RUNPOD_ALIASES = {"runpod_flux", "runpod", "flux"}


def get_backend(name: str | None, *, openai_api_key: str | None = None) -> ImageBackend:
    resolved = (name or "openai").strip().lower()
    if resolved in _RUNPOD_ALIASES:
        endpoint = os.environ.get("RUNPOD_FLUX_ENDPOINT", "")
        api_key = os.environ.get("RUNPOD_API_KEY", "")
        if not endpoint or not api_key:
            raise ImageGenerationError(
                "Image backend 'runpod_flux' selected but RUNPOD_FLUX_ENDPOINT / RUNPOD_API_KEY "
                "are not set in the environment."
            )
        return RunPodFluxBackend(api_key=api_key, endpoint=endpoint)
    return OpenAIImageBackend(api_key=openai_api_key or "")
