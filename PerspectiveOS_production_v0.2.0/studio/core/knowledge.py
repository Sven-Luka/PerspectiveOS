from dataclasses import dataclass
from pathlib import Path
import re

try:
    from ..brain.index import KnowledgeIndex
except ImportError:
    from brain.index import KnowledgeIndex
from .settings import ProjectSettings


@dataclass(frozen=True)
class RepositoryKnowledge:
    """Compatibility view of loaded repository knowledge for the Streamlit app."""

    root: Path
    documents: dict[str, str]
    loaded_documents: list[str]
    missing_documents: list[str]
    last_refresh: str

    def document(self, path: str) -> str:
        """Return a document body by repository-relative path."""
        return self.documents.get(path, "")


def repository_root() -> Path:
    return ProjectSettings().repository_root


def load_repository_knowledge(root: Path | None = None) -> RepositoryKnowledge:
    settings = ProjectSettings(repository_root=root) if root else ProjectSettings()
    index = KnowledgeIndex(settings=settings).build()
    return RepositoryKnowledge(
        root=settings.repository_root,
        documents=index.documents,
        loaded_documents=index.loaded_documents,
        missing_documents=index.missing_documents,
        last_refresh=index.last_refresh,
    )


def section(content: str, heading: str) -> str:
    match = None
    for candidate in re.finditer(r"^##\s+(.+?)\s*$", content, flags=re.MULTILINE):
        if _normalize_heading(candidate.group(1)) == _normalize_heading(heading):
            match = candidate
            break

    if match is None:
        return ""

    start = match.end()
    next_heading = re.search(r"^##\s+", content[start:], flags=re.MULTILINE)
    end = start + next_heading.start() if next_heading else len(content)
    return content[start:end].strip()


def bullets(content: str, heading: str | None = None) -> list[str]:
    target = section(content, heading) if heading else content
    return [
        line[2:].strip()
        for line in target.splitlines()
        if line.strip().startswith("- ")
    ]


def blockquotes(content: str, heading: str | None = None) -> list[str]:
    target = section(content, heading) if heading else content
    return [
        line[1:].strip()
        for line in target.splitlines()
        if line.strip().startswith(">")
    ]


def first_sentence(content: str, fallback: str) -> str:
    cleaned = " ".join(
        line.strip()
        for line in content.splitlines()
        if line.strip() and not line.strip().startswith("#")
    )
    parts = re.split(r"(?<=[.!?])\s+", cleaned)
    return parts[0] if parts and parts[0] else fallback


def _normalize_heading(value: str) -> str:
    replacements = {
        "\u00e4": "ae",
        "\u00f6": "oe",
        "\u00fc": "ue",
        "\u00c4": "ae",
        "\u00d6": "oe",
        "\u00dc": "ue",
        "\u00df": "ss",
    }
    normalized = value
    for source, replacement in replacements.items():
        normalized = normalized.replace(source, replacement)
    return re.sub(r"[^a-z0-9]+", "", normalized.lower())
