from dataclasses import dataclass, asdict
from datetime import datetime
import json
from pathlib import Path

try:
    from ..core.settings import ProjectSettings
except ImportError:
    from core.settings import ProjectSettings


@dataclass(frozen=True)
class PostPerformance:
    """Performance metrics for a published Perspective OS post."""

    post_id: str
    impressions: int = 0
    likes: int = 0
    comments: int = 0
    shares: int = 0
    saves: int = 0
    notes: str = ""
    updated_at: str = ""


class AnalyticsStore:
    """Stores future post performance data in a local JSON file."""

    def __init__(self, settings: ProjectSettings | None = None) -> None:
        """Create an analytics store using the configured Studio data directory."""
        self.settings = settings or ProjectSettings()
        self.path = self.settings.analytics_dir / "post_performance.json"

    def all(self) -> list[PostPerformance]:
        """Load all stored post performance records."""
        if not self.path.exists():
            return []
        raw_records = json.loads(self.path.read_text(encoding="utf-8"))
        return [PostPerformance(**record) for record in raw_records]

    def upsert(self, performance: PostPerformance) -> None:
        """Insert or replace a performance record by post id."""
        records = {record.post_id: record for record in self.all()}
        updated = PostPerformance(
            post_id=performance.post_id,
            impressions=performance.impressions,
            likes=performance.likes,
            comments=performance.comments,
            shares=performance.shares,
            saves=performance.saves,
            notes=performance.notes,
            updated_at=performance.updated_at or datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        )
        records[updated.post_id] = updated
        self._write(list(records.values()))

    def _write(self, records: list[PostPerformance]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = [asdict(record) for record in sorted(records, key=lambda item: item.post_id)]
        self.path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
