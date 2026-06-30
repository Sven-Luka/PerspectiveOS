"""Post-generation image fixes.

The orthosis side (anatomical LEFT leg) is something diffusion models — including
Flux — get wrong roughly half the time, no matter the prompt. The established
Perspective workflow is to MIRROR the base image rather than re-roll. This module
provides that as a deterministic flip plus an optional vision-based auto-correct:
detect which leg the knee orthosis is on and horizontally flip only when it is on
the wrong (anatomical right) leg. A horizontal mirror swaps the person's anatomical
left/right, so flipping a right-leg image yields a correct left-leg image.

Flipping the BASE photo is safe in this pipeline: base photos carry no text (text is
forbidden in them and overlays are composited later), so a mirror has no readable
side effects.
"""
import base64
import io
import json

try:
    from PIL import Image
except ImportError:  # pragma: no cover - PIL is a hard dependency of the studio
    Image = None  # type: ignore


def flip_horizontal(image_bytes: bytes) -> bytes:
    """Return the image mirrored left<->right, as PNG bytes."""
    if Image is None:
        raise RuntimeError("Pillow (PIL) is required for image post-processing.")
    image = Image.open(io.BytesIO(image_bytes))
    flipped = image.transpose(Image.FLIP_LEFT_RIGHT)
    out = io.BytesIO()
    flipped.save(out, format="PNG")
    return out.getvalue()


def _data_url(image_bytes: bytes) -> str:
    return "data:image/png;base64," + base64.b64encode(image_bytes).decode()


def detect_orthosis_side(
    image_bytes: bytes, api_key: str, model: str = "gpt-5.5"
) -> str:
    """Ask the vision model which leg the knee orthosis is on.

    Returns "left" / "right" (the person's ANATOMICAL side) or "unknown".
    Never raises: any failure returns "unknown" so callers can no-op safely.
    """
    if not api_key:
        return "unknown"
    try:
        from openai import OpenAI
    except ImportError:
        return "unknown"

    prompt = (
        "Look at the person in this photo. They wear a knee orthosis (a brace with side "
        "hinges and a blue padded knee section) on exactly one leg. Determine which of the "
        "person's OWN legs it is on — their anatomical left or right — taking the camera view "
        "into account (in a rear view the person's left leg is on the image's right side; in a "
        "front view it is on the image's left side). Reply with ONLY compact JSON: "
        '{"side": "left" | "right" | "unknown"}. Use "unknown" if no orthosis is visible or you '
        "cannot tell."
    )
    try:
        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": _data_url(image_bytes)}},
                    ],
                }
            ],
        )
        content = response.choices[0].message.content or "{}"
        start, end = content.find("{"), content.rfind("}")
        payload = json.loads(content[start : end + 1]) if start >= 0 and end > start else {}
        side = str(payload.get("side", "unknown")).strip().lower()
        return side if side in ("left", "right") else "unknown"
    except Exception:
        return "unknown"


def ensure_orthosis_left(
    image_bytes: bytes, api_key: str, model: str = "gpt-5.5"
) -> tuple[bytes, str]:
    """Return (image_bytes, action) with the orthosis on the anatomical LEFT leg.

    action is "flipped" (was on the right, mirrored), "kept" (already left), or
    "skipped" (unknown / no detection). Mirrors deterministically; no re-generation.
    """
    side = detect_orthosis_side(image_bytes, api_key, model)
    if side == "right":
        return flip_horizontal(image_bytes), "flipped"
    if side == "left":
        return image_bytes, "kept"
    return image_bytes, "skipped"
