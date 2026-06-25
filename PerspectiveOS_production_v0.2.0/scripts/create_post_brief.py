from pathlib import Path
import sys
from datetime import date

template = """# {title}

## Serie
...

## Hook
...

## Warum-Satz
...

## Metapher
...

## Carousel-Struktur

### Slide 1
Hook:

### Slide 2
Reality Moment:

### Slide 3
Perspektivwechsel:

### Slide 4
Warm Ending:

## Caption
...

## Design-Hinweise
- 1080 × 1350 px
- natürlicher Smartphone-Look
- viel Bild, wenig Text
"""

def slugify(s: str) -> str:
    return "".join(c.lower() if c.isalnum() else "_" for c in s).strip("_")

if __name__ == "__main__":
    title = " ".join(sys.argv[1:]) or "Neuer Beitrag"
    out = Path("posts/drafts") / f"{date.today()}_{slugify(title)}.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(template.format(title=title), encoding="utf-8")
    print(out)
