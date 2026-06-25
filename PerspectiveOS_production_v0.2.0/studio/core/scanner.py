from dataclasses import dataclass
from pathlib import Path

from .settings import ProjectSettings


@dataclass(frozen=True)
class MarkdownDocument:
    """A Markdown document discovered inside the Perspective OS repository."""

    path: Path
    relative_path: str
    content: str


class RepositoryScanner:
    """Scans the repository and reads Markdown source files for Studio services."""

    def __init__(self, settings: ProjectSettings | None = None) -> None:
        """Create a scanner using the provided settings or default project settings."""
        self.settings = settings or ProjectSettings()

    def read_markdown_files(self) -> list[MarkdownDocument]:
        """Read all Markdown files below the configured repository root."""
        documents: list[MarkdownDocument] = []
        for path in sorted(self.settings.repository_root.glob(self.settings.markdown_glob)):
            if not path.is_file():
                continue
            relative_path = path.relative_to(self.settings.repository_root).as_posix()
            documents.append(
                MarkdownDocument(
                    path=path,
                    relative_path=relative_path,
                    content=path.read_text(encoding="utf-8"),
                )
            )
        return documents

    def read_selected_markdown(self, relative_paths: tuple[str, ...]) -> tuple[dict[str, str], list[str], list[str]]:
        """Read selected Markdown files and return loaded content plus missing paths."""
        documents: dict[str, str] = {}
        loaded: list[str] = []
        missing: list[str] = []

        for relative_path in relative_paths:
            source_path = self.settings.repository_root / relative_path
            if source_path.exists():
                documents[relative_path] = source_path.read_text(encoding="utf-8")
                loaded.append(relative_path)
            else:
                missing.append(relative_path)

        return documents, loaded, missing
