from dataclasses import dataclass
from pathlib import Path

try:
    from ..core.settings import ProjectSettings
except ImportError:
    from core.settings import ProjectSettings


@dataclass(frozen=True)
class AssetRecord:
    """A discovered image asset and any Markdown metadata associated with it."""

    path: Path
    relative_path: str
    asset_type: str
    metadata: str


class AssetRegistry:
    """Reads future image assets and Markdown metadata from the repository asset tree."""

    IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}

    def __init__(self, settings: ProjectSettings | None = None) -> None:
        """Create an asset registry using the configured asset directory."""
        self.settings = settings or ProjectSettings()

    def scan(self) -> list[AssetRecord]:
        """Return all discovered image assets with best-effort metadata."""
        assets_dir = self.settings.assets_dir
        if not assets_dir.exists():
            return []

        records: list[AssetRecord] = []
        for path in sorted(assets_dir.rglob("*")):
            if not path.is_file() or path.suffix.lower() not in self.IMAGE_EXTENSIONS:
                continue
            relative_path = path.relative_to(self.settings.repository_root).as_posix()
            records.append(
                AssetRecord(
                    path=path,
                    relative_path=relative_path,
                    asset_type=path.parent.name,
                    metadata=self._read_metadata_for(path),
                )
            )
        return records

    def _read_metadata_for(self, image_path: Path) -> str:
        sidecar = image_path.with_suffix(".md")
        if sidecar.exists():
            return sidecar.read_text(encoding="utf-8")
        catalog = self.settings.assets_dir / "ASSET_CATALOG.md"
        if catalog.exists():
            return catalog.read_text(encoding="utf-8")
        return ""
