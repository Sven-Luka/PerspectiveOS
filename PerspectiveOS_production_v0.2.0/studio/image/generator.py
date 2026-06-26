import base64
from dataclasses import dataclass
from pathlib import Path


# gpt-image-1 supports a fixed set of sizes. Map our publishing formats to the
# closest available aspect ratio (portrait for feed/story, square for covers).
FORMAT_SIZES = {
    "Feed 4:5": "1024x1536",
    "Story 9:16": "1024x1536",
    "Reel Cover": "1024x1024",
}
DEFAULT_SIZE = "1024x1536"


@dataclass(frozen=True)
class GeneratedImage:
    """A generated image and where it was written on disk."""

    path: Path
    relative_path: str
    file_name: str
    image_bytes: bytes


class ImageGenerationError(RuntimeError):
    """Raised when image generation fails for a reportable reason."""


class ImageGenerator:
    """Generates production images from an image prompt using OpenAI gpt-image-1."""

    MODEL = "gpt-image-1"

    def __init__(self, api_key: str, model: str | None = None) -> None:
        """Create a generator bound to an OpenAI API key."""
        if not api_key:
            raise ImageGenerationError(
                "No OpenAI API key provided. Set OPENAI_API_KEY or enter a key in the sidebar."
            )
        self.api_key = api_key
        self.model = model or self.MODEL

    def generate(
        self,
        prompt: str,
        folder_path: Path,
        format_name: str = "Feed 4:5",
        file_name: str = "image.png",
        repository_root: Path | None = None,
    ) -> GeneratedImage:
        """Generate one image from the prompt and write it into the folder."""
        try:
            from openai import OpenAI
        except ImportError as exc:  # pragma: no cover - dependency hint
            raise ImageGenerationError(
                "The 'openai' package is not installed. Run: pip install -r requirements.txt"
            ) from exc

        client = OpenAI(api_key=self.api_key)
        size = FORMAT_SIZES.get(format_name, DEFAULT_SIZE)

        try:
            result = client.images.generate(
                model=self.model,
                prompt=prompt,
                size=size,
                quality="high",
                n=1,
            )
        except Exception as exc:  # surface API/auth/quota errors to the UI
            raise ImageGenerationError(f"Image generation failed: {exc}") from exc

        image_bytes = base64.b64decode(result.data[0].b64_json)

        folder_path.mkdir(parents=True, exist_ok=True)
        image_path = folder_path / file_name
        image_path.write_bytes(image_bytes)

        return GeneratedImage(
            path=image_path,
            relative_path=self._display_path(image_path, repository_root),
            file_name=file_name,
            image_bytes=image_bytes,
        )

    def generate_with_references(
        self,
        prompt: str,
        reference_paths: list[Path],
        folder_path: Path,
        format_name: str = "Feed 4:5",
        file_name: str = "image.png",
        repository_root: Path | None = None,
    ) -> GeneratedImage:
        """Generate an image using selected reference images as visual inputs."""
        existing_references = [path for path in reference_paths if path.exists()]
        if not existing_references:
            return self.generate(prompt, folder_path, format_name, file_name, repository_root)

        try:
            from openai import OpenAI
        except ImportError as exc:  # pragma: no cover - dependency hint
            raise ImageGenerationError(
                "The 'openai' package is not installed. Run: pip install -r requirements.txt"
            ) from exc

        client = OpenAI(api_key=self.api_key)
        size = FORMAT_SIZES.get(format_name, DEFAULT_SIZE)

        handles = [path.open("rb") for path in existing_references]
        try:
            result = client.images.edit(
                model=self.model,
                image=handles,
                prompt=prompt,
                size=size,
                quality="high",
                n=1,
            )
        except TypeError as exc:
            raise ImageGenerationError(
                "Reference-guided image generation is not supported by the installed OpenAI SDK. "
                "Update the 'openai' package from requirements.txt."
            ) from exc
        except Exception as exc:  # surface API/auth/quota errors to the UI
            raise ImageGenerationError(f"Reference-guided image generation failed: {exc}") from exc
        finally:
            for handle in handles:
                handle.close()

        image_bytes = base64.b64decode(result.data[0].b64_json)

        folder_path.mkdir(parents=True, exist_ok=True)
        image_path = folder_path / file_name
        image_path.write_bytes(image_bytes)

        return GeneratedImage(
            path=image_path,
            relative_path=self._display_path(image_path, repository_root),
            file_name=file_name,
            image_bytes=image_bytes,
        )

    def _display_path(self, path: Path, repository_root: Path | None) -> str:
        if repository_root is not None:
            try:
                return path.relative_to(repository_root).as_posix()
            except ValueError:
                pass
        return path.as_posix()
