from dataclasses import dataclass


@dataclass(frozen=True)
class ProductionRequest:
    """User-selected inputs for a Perspective Studio production folder."""

    topic: str
    target_emotion: str
    image_type: str
    location: str = ""
    outfit: str = ""
    aid_visibility: str = "subtle"
    metaphor: str = ""
    format_name: str = "Feed 4:5"
    free_story: str = ""
    include_outfit_tip: bool = False
    outfit_source_url: str = ""

    @property
    def requested_metaphor(self) -> str:
        """Return the requested metaphor or a deterministic fallback marker."""
        return self.metaphor.strip() or "repository-selected metaphor"


@dataclass(frozen=True)
class ProductionFolder:
    """Result of a production folder generation run."""

    folder_name: str
    relative_path: str
    files: dict[str, str]
