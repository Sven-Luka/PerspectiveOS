from datetime import date
from pathlib import Path
import re

from .settings import ProjectSettings


def slugify(value: str) -> str:
    normalized = value.strip().lower()
    normalized = re.sub(r"[^a-z0-9]+", "_", normalized)
    return normalized.strip("_") or "post"


def save_brief(topic: str, content: str) -> Path:
    generated_dir = ProjectSettings().generated_dir
    generated_dir.mkdir(parents=True, exist_ok=True)

    output_path = generated_dir / f"{date.today().isoformat()}_{slugify(topic)}.md"
    output_path.write_text(content, encoding="utf-8")
    return output_path
