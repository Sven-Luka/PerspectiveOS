import json
from dataclasses import dataclass
from pathlib import Path

try:
    from ..core.settings import ProjectSettings
except ImportError:
    from core.settings import ProjectSettings


PRIORITY_WEIGHT = {
    "master": 40,
    "approved": 25,
    "reference": 10,
}


@dataclass(frozen=True)
class ReferenceImage:
    """A selected reference image from the repository reference library."""

    id: str
    path: Path
    relative_path: str
    category: str
    priority: str
    description: str
    usage: str
    score: int

    def to_dict(self) -> dict[str, object]:
        return {
            "id": self.id,
            "path": self.relative_path,
            "category": self.category,
            "priority": self.priority,
            "description": self.description,
            "usage": self.usage,
            "score": self.score,
        }


class ReferenceSelector:
    """Selects approved visual references for a production request."""

    INDEX_PATH = "assets/references/ASSET_INDEX.json"

    def __init__(self, settings: ProjectSettings | None = None) -> None:
        self.settings = settings or ProjectSettings()

    def select(
        self,
        *,
        topic: str,
        location: str,
        outfit: str,
        aid_visibility: str,
        limit: int = 8,
    ) -> list[ReferenceImage]:
        records = self._load_index()
        selected: list[ReferenceImage] = []
        seen_paths: set[str] = set()

        for record in records:
            if not self._usable(record):
                continue
            score = self._score(record, topic, location, outfit, aid_visibility)
            if score <= 0:
                continue
            path = str(record.get("path", ""))
            if path in seen_paths:
                continue
            seen_paths.add(path)
            selected.append(self._reference(record, score))

        return _with_required_groups(
            sorted(selected, key=lambda item: item.score, reverse=True),
            required_prefixes=("layouts/", "character/", "orthosis/"),
            limit=limit,
        )

    def manifest_markdown(self, references: list[ReferenceImage]) -> str:
        lines = [
            "# Reference Manifest",
            "",
            "These references are used to keep the generated image aligned with Perspective OS.",
            "They are reference inputs, not publishable final artwork.",
            "",
            "## Selected References",
        ]
        if not references:
            lines.append("- No references selected.")
        for reference in references:
            lines.append(
                f"- `{reference.relative_path}` ({reference.category}, {reference.priority}, score {reference.score}): "
                f"{reference.description}"
            )
        return "\n".join(lines) + "\n"

    def manifest_json(self, references: list[ReferenceImage]) -> str:
        payload = {
            "version": "visual-agent-v1",
            "references": [reference.to_dict() for reference in references],
        }
        return json.dumps(payload, indent=2, ensure_ascii=False)

    def _load_index(self) -> list[dict[str, object]]:
        index_path = self.settings.repository_root / self.INDEX_PATH
        if not index_path.exists():
            return []
        return json.loads(index_path.read_text(encoding="utf-8"))

    def _usable(self, record: dict[str, object]) -> bool:
        category = str(record.get("category", "")).lower()
        priority = str(record.get("priority", "")).lower()
        path = str(record.get("path", ""))
        if "rejected" in category or priority == "rejected":
            return False
        if not path:
            return False
        return (self.settings.repository_root / path).exists()

    def _score(
        self,
        record: dict[str, object],
        topic: str,
        location: str,
        outfit: str,
        aid_visibility: str,
    ) -> int:
        category = str(record.get("category", "")).lower()
        description = str(record.get("description", "")).lower()
        priority = str(record.get("priority", "")).lower()
        haystack = f"{category} {description}"
        request_text = f"{topic} {location} {outfit} {aid_visibility}".lower()

        score = PRIORITY_WEIGHT.get(priority, 5)
        if "layouts/" in category:
            score += 35
        if "character/body_silhouette" in category:
            score += 35
        if "orthosis/" in category:
            score += 30
        if "outfits/" in category:
            score += 20
        if "locations/" in category:
            score += 15
        if "diapers/" in category and any(term in request_text for term in ("diaper", "incontinence", "windel")):
            score += 35
        if "train" in category and any(term in request_text for term in ("zug", "bahn", "train")):
            score += 35
        if "home_office" in category and any(term in request_text for term in ("wohnung", "zuhause", "home")):
            score += 25
        if "black_polo_black_shorts" in category and any(term in request_text for term in ("shorts", "polo")):
            score += 25
        if "tights_black" in category and any(term in request_text for term in ("strumpfhose", "tights", "leggings")):
            score += 25
        if any(term in haystack for term in ("gesicht", "face")):
            score += 5
        return score

    def _reference(self, record: dict[str, object], score: int) -> ReferenceImage:
        relative_path = str(record["path"])
        return ReferenceImage(
            id=str(record.get("id", "")),
            path=self.settings.repository_root / relative_path,
            relative_path=relative_path,
            category=str(record.get("category", "")),
            priority=str(record.get("priority", "")),
            description=str(record.get("description", "")),
            usage=str(record.get("usage", "")),
            score=score,
        )


def _with_required_groups(
    references: list[ReferenceImage],
    *,
    required_prefixes: tuple[str, ...],
    limit: int,
) -> list[ReferenceImage]:
    selected: list[ReferenceImage] = []
    selected_paths: set[str] = set()

    for prefix in required_prefixes:
        match = next(
            (reference for reference in references if reference.category.startswith(prefix)),
            None,
        )
        if match is not None:
            selected.append(match)
            selected_paths.add(match.relative_path)

    for reference in references:
        if len(selected) >= limit:
            break
        if reference.relative_path in selected_paths:
            continue
        selected.append(reference)
        selected_paths.add(reference.relative_path)

    return selected
