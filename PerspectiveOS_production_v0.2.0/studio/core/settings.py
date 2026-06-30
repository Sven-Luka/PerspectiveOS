from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class ProjectSettings:
    """Central configuration for Perspective Studio paths and source documents."""

    repository_root: Path = field(default_factory=lambda: Path(__file__).resolve().parents[2])
    studio_root: Path = field(default_factory=lambda: Path(__file__).resolve().parents[1])
    generated_dir_name: str = "generated"
    assets_dir_name: str = "assets"
    analytics_dir_name: str = "analytics_data"
    # Image generation backend: "openai" (gpt-image-1) or "runpod_flux" (RunPod ComfyUI/Flux).
    # Overridable at runtime via the IMAGE_BACKEND env var.
    image_backend: str = "openai"
    markdown_glob: str = "**/*.md"
    required_knowledge_documents: tuple[str, ...] = (
        "creative/CreatorBible.md",
        "creative/LanguageBible.md",
        "creative/MetaphorLibrary.md",
        "visual/DesignSystem.md",
        "visual/CarouselSystem.md",
        "visual/PhotoStyle.md",
        "prompts/image/master_image_prompt.md",
        "persona/Character.md",
        "persona/Incontinence.md",
        "persona/Orthosis.md",
        "persona/OutfitGuide.md",
        "persona/TightsGuide.md",
    )
    index_documents: tuple[str, ...] = (
        "creative/CreatorBible.md",
        "creative/LanguageBible.md",
        "visual/DesignSystem.md",
        "visual/CarouselSystem.md",
        "persona/Character.md",
        "persona/Incontinence.md",
        "persona/Orthosis.md",
        "persona/OutfitGuide.md",
    )

    @property
    def generated_dir(self) -> Path:
        """Return the directory where generated production briefs are written."""
        return self.studio_root / self.generated_dir_name

    @property
    def assets_dir(self) -> Path:
        """Return the repository asset directory."""
        return self.repository_root / self.assets_dir_name

    @property
    def analytics_dir(self) -> Path:
        """Return the local Studio analytics storage directory."""
        return self.studio_root / self.analytics_dir_name

    @property
    def validated_posts_dir(self) -> Path:
        """Return the curated local library of highly rated production outputs."""
        return self.analytics_dir / "validated_posts"
