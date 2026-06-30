"""Image-backend abstraction.

A backend turns a finished generation prompt (+ optional reference image paths and
a target ``WxH`` size) into raw image bytes. This is the single seam that lets the
pipeline swap OpenAI gpt-image-1 for the RunPod/Flux backend without touching the
orchestrator, layout, or review code.
"""
from abc import ABC, abstractmethod
from pathlib import Path

try:
    from ..generator import ImageGenerationError
except ImportError:
    from image.generator import ImageGenerationError

__all__ = ["ImageBackend", "ImageGenerationError"]


class ImageBackend(ABC):
    """Generates image bytes from a prompt. Implementations are provider-specific."""

    name: str = "base"

    @abstractmethod
    def generate(
        self,
        *,
        prompt: str,
        reference_paths: list[Path],
        size: str,
    ) -> bytes:
        """Return the raw bytes of one generated image (PNG/WebP).

        ``size`` is a ``"<width>x<height>"`` string. ``reference_paths`` may be empty;
        a backend that cannot use references should ignore them (and ideally log it).
        """
        raise NotImplementedError
