from datetime import date
from pathlib import Path

try:
    from ..brain.index import IndexedKnowledge
    from ..core.settings import ProjectSettings
    from ..core.storage import slugify
except ImportError:
    from brain.index import IndexedKnowledge
    from core.settings import ProjectSettings
    from core.storage import slugify
from .artifacts import ProductionArtifactGenerator
from .models import ProductionFolder, ProductionRequest
from .review import ProductionReviewer


class ProductionFolderPipeline:
    """Creates complete production folders for Perspective Studio outputs."""

    def __init__(
        self,
        knowledge: IndexedKnowledge,
        settings: ProjectSettings | None = None,
    ) -> None:
        """Create a pipeline using repository knowledge and optional settings."""
        self.knowledge = knowledge
        self.settings = settings or ProjectSettings()
        self.artifacts = ProductionArtifactGenerator(knowledge)
        self.reviewer = ProductionReviewer(knowledge)

    def create(self, request: ProductionRequest) -> ProductionFolder:
        """Create a dated production folder and write all generated artifacts."""
        folder_name = f"{date.today().isoformat()}_{slugify(request.topic)}"
        folder_path = self.settings.generated_dir / folder_name
        folder_path.mkdir(parents=True, exist_ok=True)

        files = self.artifacts.generate_all(request)
        review = self.reviewer.review(files)
        files["automation_review.md"] = review.to_markdown()
        files["automation_review.json"] = review.to_json()
        for file_name, content in files.items():
            self._write(folder_path / file_name, content)

        return ProductionFolder(
            folder_name=folder_name,
            relative_path=self._display_path(folder_path),
            files=files,
        )

    def _write(self, path: Path, content: str) -> None:
        path.write_text(content, encoding="utf-8")

    def _display_path(self, path: Path) -> str:
        try:
            return path.relative_to(self.settings.repository_root).as_posix()
        except ValueError:
            return path.as_posix()
