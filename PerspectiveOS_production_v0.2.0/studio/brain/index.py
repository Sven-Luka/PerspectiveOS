from dataclasses import dataclass
from datetime import datetime

try:
    from ..core.scanner import RepositoryScanner
    from ..core.settings import ProjectSettings
except ImportError:
    from core.scanner import RepositoryScanner
    from core.settings import ProjectSettings


@dataclass(frozen=True)
class IndexedKnowledge:
    """Structured knowledge loaded from the Perspective OS repository."""

    documents: dict[str, str]
    loaded_documents: list[str]
    missing_documents: list[str]
    last_refresh: str

    def document(self, path: str) -> str:
        """Return a document body by repository-relative path."""
        return self.documents.get(path, "")


class KnowledgeIndex:
    """Builds the Studio knowledge index from canonical repository documents."""

    def __init__(
        self,
        scanner: RepositoryScanner | None = None,
        settings: ProjectSettings | None = None,
    ) -> None:
        """Create an index builder with an optional scanner and settings object."""
        self.settings = settings or ProjectSettings()
        self.scanner = scanner or RepositoryScanner(self.settings)

    def build(self) -> IndexedKnowledge:
        """Build an index of Creator Bible, Language Bible, Design System, and Persona documents."""
        documents, loaded, missing = self.scanner.read_selected_markdown(
            self.settings.required_knowledge_documents
        )
        return IndexedKnowledge(
            documents=documents,
            loaded_documents=loaded,
            missing_documents=missing,
            last_refresh=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        )
