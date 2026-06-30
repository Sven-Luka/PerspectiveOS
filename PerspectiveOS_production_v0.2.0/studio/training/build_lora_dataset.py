"""Build the persona LoRA training dataset from the reference library.

Pulls the unique persona images (character / orthosis / outfits) from
``assets/references/ASSET_INDEX.json``, dedupes by content hash, resizes each to a
1024 long edge, and writes one image + one caption ``.txt`` per sample into the output
directory — ready for ai-toolkit / kohya Flux LoRA training. No network, no cost.

Captions use a trigger word (default ``j0na``) and tag the outfit/orthosis visible in the
image. The persona is deliberately faceless, so captions never describe a face/identity.

Usage:
    python studio/training/build_lora_dataset.py [--out DIR] [--trigger j0na] [--size 1024]
"""
import argparse
import json
from collections import OrderedDict
from pathlib import Path

from PIL import Image

REPO = Path(__file__).resolve().parents[2]
INDEX = REPO / "assets/references/ASSET_INDEX.json"
PERSONA_PREFIXES = ("character/", "orthosis/", "outfits/")

# Reference category -> English caption fragment for that visible element.
TAG_MAP = {
    "character/body_silhouette": "androgynous slim person, full body",
    "orthosis/front": "blue Bauerfeind knee orthosis on the left leg",
    "orthosis/side": "blue knee orthosis seen from the side",
    "orthosis/details": "knee orthosis hinges and velcro straps, close detail",
    "outfits/black_polo_black_shorts": "black polo shirt and black shorts",
    "outfits/tights_black": "black opaque tights",
}


def build_caption(trigger: str, categories: list[str]) -> str:
    fragments: list[str] = []
    for category in categories:
        tag = TAG_MAP.get(category)
        if tag and tag not in fragments:
            fragments.append(tag)
    body = ", ".join(fragments) if fragments else "androgynous person"
    return f"{trigger}, {body}, everyday documentary photo, hair tied back, face not visible"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default=str(REPO / "studio/generated/lora_dataset/jona"))
    parser.add_argument("--trigger", default="j0na")
    parser.add_argument("--size", type=int, default=1024)
    args = parser.parse_args()

    records = json.loads(INDEX.read_text(encoding="utf-8"))

    # Aggregate ALL categories an image appears in, deduped by content hash, so we can
    # both caption from its persona categories and exclude it if it is also a diaper/product
    # shot (those are cross-listed under outfits/tights_black but belong to the separate
    # TENA concept, not the persona LoRA v1).
    by_image: "OrderedDict[str, dict]" = OrderedDict()
    for record in records:
        category = str(record.get("category", ""))
        if str(record.get("priority", "")).lower() == "rejected" or "rejected" in category:
            continue
        key = str(record.get("sha1") or record.get("path"))
        entry = by_image.setdefault(key, {"categories": [], "paths": []})
        entry["categories"].append(category)
        if record.get("path"):
            entry["paths"].append(str(record["path"]))

    def is_persona(categories: list[str]) -> bool:
        has_persona = any(c.startswith(PERSONA_PREFIXES) for c in categories)
        is_product = any(c.startswith("diapers/") for c in categories)
        return has_persona and not is_product

    by_image = OrderedDict((k, v) for k, v in by_image.items() if is_persona(v["categories"]))

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    count = 0
    for entry in by_image.values():
        source = next((REPO / p for p in entry["paths"] if (REPO / p).exists()), None)
        if source is None:
            continue
        image = Image.open(source).convert("RGB")
        image.thumbnail((args.size, args.size), Image.LANCZOS)
        stem = source.stem
        image.save(out_dir / f"{stem}.jpg", "JPEG", quality=95)
        caption = build_caption(args.trigger, entry["categories"])
        (out_dir / f"{stem}.txt").write_text(caption, encoding="utf-8")
        count += 1
        print(f"  {stem}: {caption}")

    print(f"\n{count} training samples -> {out_dir}")
    print("Next: upload this folder to the RunPod network volume and train with ai-toolkit "
          "(base black-forest-labs/FLUX.1-dev). See studio/FLUX_PHASE3_LORA_PLAN.md.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
