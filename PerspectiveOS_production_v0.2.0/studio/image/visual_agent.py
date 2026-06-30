import os
from dataclasses import dataclass
from pathlib import Path
import re

try:
    from ..brain.index import IndexedKnowledge
    from ..core.settings import ProjectSettings
except ImportError:
    from brain.index import IndexedKnowledge
    from core.settings import ProjectSettings

from .generator import DEFAULT_SIZE, FORMAT_SIZES, GeneratedImage
from .backends import get_backend
from .layout_composer import ComposedLayout, LayoutComposer, LayoutContent
from .prompt_contract import ImagePromptContractBuilder
from .reference_selector import ReferenceImage, ReferenceSelector
from .vision_review import VisionReviewer, VisualReview


@dataclass(frozen=True)
class VisualAgentResult:
    """Result of one reference-guided visual agent run."""

    image: GeneratedImage
    layout: ComposedLayout | None
    carousel_layouts: list[ComposedLayout]
    references: list[ReferenceImage]
    review: VisualReview
    # Per-slide overlay text + the base photo each slide was composed on, so the UI
    # can re-edit the overlay text and recompose without regenerating the photos.
    slide_contents: list[LayoutContent]
    base_image_paths: list[Path]


class VisualAgent:
    """Runs the v1 reference-guided image generation workflow."""

    def __init__(
        self,
        api_key: str,
        knowledge: IndexedKnowledge,
        settings: ProjectSettings | None = None,
    ) -> None:
        self.api_key = api_key
        self.knowledge = knowledge
        self.settings = settings or ProjectSettings()
        self.references = ReferenceSelector(self.settings)
        backend_name = os.environ.get("IMAGE_BACKEND", "") or getattr(
            self.settings, "image_backend", "openai"
        )
        self.backend = get_backend(backend_name, openai_api_key=api_key)
        self.composer = LayoutComposer(self.settings)
        self.contract_builder = ImagePromptContractBuilder(knowledge)
        self.reviewer = VisionReviewer(api_key=api_key)

    def run(
        self,
        *,
        prompt: str,
        folder_path: Path,
        format_name: str,
        topic: str,
        location: str,
        outfit: str,
        aid_visibility: str,
        repository_root: Path | None = None,
        carousel_content: str = "",
    ) -> VisualAgentResult:
        references = self.references.select(
            topic=topic,
            location=location,
            outfit=outfit,
            aid_visibility=aid_visibility,
            limit=16,
        )
        folder_path.mkdir(parents=True, exist_ok=True)
        self._write_manifest(folder_path, references)

        request_text = f"{topic} {aid_visibility}".lower()
        prioritize_diaper = any(
            term in request_text
            for term in ("windel", "diaper", "incontinence", "inkontinenz", "tena", "slip", "bund", "saugkern")
        )
        aid_lower = aid_visibility.lower()
        aid_on_body = aid_lower.startswith(("diaper", "both")) or any(
            term in aid_lower
            for term in ("getragen", "am körper", "am koerper", "durchschimmer", "über den bund",
                         "ueber den bund", "windelbund", "unter der strumpfhose", "unter strumpfhose", "kontur")
        )
        # Discreet/subtle posts must not foreground the product: this drives a softer prompt and a
        # standing/full-body slide framing that the output moderation accepts far more reliably.
        discreet = not aid_on_body
        generation_references = [
            reference.path
            for reference in self._generation_references(references, prioritize_diaper, aid_on_body)
        ]

        image = self._generate_image(
            prompt=prompt,
            reference_paths=generation_references,
            folder_path=folder_path,
            format_name=format_name,
            repository_root=repository_root,
            file_name="image.png",
            discreet=discreet,
        )
        base_images = [image]
        for slide_number in (2, 3, 4):
            base_images.append(
                self._generate_image(
                    prompt=self._slide_prompt(prompt, slide_number, discreet=discreet),
                    reference_paths=generation_references,
                    folder_path=folder_path,
                    format_name=format_name,
                    repository_root=repository_root,
                    file_name=f"image_slide_{slide_number:02d}.png",
                    discreet=discreet,
                )
            )
        contract = self.contract_builder.build()
        base_image_paths = [base_image.path for base_image in base_images]
        carousel_layouts, slide_contents = self._compose_carousel_layouts(
            image_paths=base_image_paths,
            folder_path=folder_path,
            topic=topic,
            prompt=prompt,
            carousel_content=carousel_content,
            repository_root=repository_root,
        )
        layout = carousel_layouts[0] if carousel_layouts else None
        review = self.reviewer.review(
            image_path=image.path,
            prompt=prompt,
            format_name=format_name,
            contract=contract,
            references=references,
            carousel_source_count=len(base_images),
        )
        (folder_path / "image_review.md").write_text(review.to_markdown(), encoding="utf-8")
        (folder_path / "image_review.json").write_text(review.to_json(), encoding="utf-8")
        return VisualAgentResult(
            image=image,
            layout=layout,
            carousel_layouts=carousel_layouts,
            references=references,
            review=review,
            slide_contents=slide_contents,
            base_image_paths=base_image_paths,
        )

    def _compose_carousel_layouts(
        self,
        *,
        image_paths: list[Path],
        folder_path: Path,
        topic: str,
        prompt: str,
        carousel_content: str,
        repository_root: Path | None,
    ) -> tuple[list[ComposedLayout], list[LayoutContent]]:
        custom_contents = _layout_contents_from_carousel(carousel_content, topic)
        if custom_contents:
            layouts = self.composer.compose_carousel(
                source_images=image_paths,
                folder_path=folder_path,
                contents=custom_contents,
                repository_root=repository_root,
            )
            return layouts, custom_contents
        slide_count = 4
        contents = [
            LayoutContent(
                series_label=topic or "Anders gedacht",
                headline=_first_prompt_line(prompt, fallback="Die beste Windel bringt nichts..."),
                highlight=_highlight_line(prompt, fallback="...wenn man sie falsch benutzt."),
                icon_labels=("Drang nicht aufhalten", "Richtiger Sitz", "Body oder enger Slip"),
                slide_number=1,
                slide_count=slide_count,
                slide_kind="hook",
            ),
            LayoutContent(
                series_label=topic or "Anders gedacht",
                headline="Sitz entscheidet.",
                highlight="kurz prüfen, länger entspannt sein.",
                body_text="Nicht zu locker, nicht zu eng. Alltag zuerst, Hilfsmittel begleitet.",
                icon_labels=("Auslaufbündchen", "richtige Größe", "nicht zu locker"),
                slide_number=2,
                slide_count=slide_count,
                slide_kind="detail",
            ),
            LayoutContent(
                series_label=topic or "Anders gedacht",
                headline="Body oder enger Slip.",
                highlight="einfach besser unterwegs.",
                body_text="Hält, was halten soll, ohne dass der ganze Tag darum kreist.",
                icon_labels=("Halt", "Outfit", "Freiheit"),
                slide_number=3,
                slide_count=slide_count,
                slide_kind="detail",
            ),
            LayoutContent(
                series_label="Perspective",
                headline="Folge mir",
                highlight="für ehrliche Einblicke",
                body_text="mit Humor und Haltung.",
                icon_labels=("Ehrlich.", "Mutmachend.", "Anders."),
                slide_number=4,
                slide_count=slide_count,
                slide_kind="cta",
            ),
        ]
        layouts = self.composer.compose_carousel(
            source_images=image_paths,
            folder_path=folder_path,
            contents=contents,
            repository_root=repository_root,
        )
        return layouts, contents

    def _generation_references(
        self, references: list[ReferenceImage], prioritize_diaper: bool = False, aid_on_body: bool = True
    ) -> list[ReferenceImage]:
        """Return the focused subset of references that should be attached to image generation.

        ``prioritize_diaper`` means the post is about the incontinence product. Only when
        ``aid_on_body`` is also set (the diaper is meant to be visible worn on the body) do we
        attach the worn close-up crop; otherwise we attach the standalone/in-hand product only.
        The worn underwear-like crops bias the edit model toward a lower-body composition that
        OpenAI's output moderation tends to reject, so we keep them out of discreet scenes.
        """
        selected: list[ReferenceImage] = []
        seen_paths: set[str] = set()
        seen_ids: set[str] = set()
        blocked_prefixes = (
            "layouts/",
            "rejected/",
            "orthosis/details",
            "diapers/details_closeup",
        )
        if prioritize_diaper and aid_on_body:
            preferred_prefixes = (
                "character/body_silhouette",
                "orthosis/front",
                "diapers/tena_worn",
                "diapers/tena_product",
                "orthosis/side",
                "locations/",
                "outfits/",
                "diapers/",
            )
            cap = 5
        elif prioritize_diaper:
            # diaper relevant but discreet (in hand/bag, subtle) -> product only, no worn crop
            preferred_prefixes = (
                "character/body_silhouette",
                "orthosis/front",
                "diapers/tena_product",
                "diapers/product_in_hand",
                "orthosis/side",
                "locations/",
                "outfits/",
            )
            cap = 5
            blocked_prefixes = blocked_prefixes + (
                "diapers/tena_worn",
                "diapers/waistband_visible",
                "diapers/under_clothes_silhouette",
            )
        else:
            preferred_prefixes = (
                "character/body_silhouette",
                "orthosis/front",
                "orthosis/side",
                "locations/",
                "outfits/",
                "diapers/",
            )
            cap = 4

        for prefix in preferred_prefixes:
            for reference in references:
                if len(selected) >= cap:
                    return selected
                if any(reference.category.startswith(blocked) for blocked in blocked_prefixes):
                    continue
                if not reference.category.startswith(prefix):
                    continue
                if reference.relative_path in seen_paths:
                    continue
                if (
                    reference.id
                    and reference.id in seen_ids
                    and not reference.category.startswith("orthosis/")
                ):
                    continue
                selected.append(reference)
                seen_paths.add(reference.relative_path)
                if reference.id:
                    seen_ids.add(reference.id)
                break
        return selected

    def prepare_only(
        self,
        *,
        folder_path: Path,
        topic: str,
        location: str,
        outfit: str,
        aid_visibility: str,
    ) -> list[ReferenceImage]:
        references = self.references.select(
            topic=topic,
            location=location,
            outfit=outfit,
            aid_visibility=aid_visibility,
        )
        folder_path.mkdir(parents=True, exist_ok=True)
        self._write_manifest(folder_path, references)
        return references

    def _write_manifest(self, folder_path: Path, references: list[ReferenceImage]) -> None:
        (folder_path / "reference_manifest.md").write_text(
            self.references.manifest_markdown(references),
            encoding="utf-8",
        )
        (folder_path / "reference_manifest.json").write_text(
            self.references.manifest_json(references),
            encoding="utf-8",
        )

    def _generate_image(
        self,
        *,
        prompt: str,
        reference_paths: list[Path],
        folder_path: Path,
        format_name: str,
        repository_root: Path | None,
        file_name: str = "image.png",
        discreet: bool = True,
    ) -> GeneratedImage:
        existing_references = [path for path in reference_paths if path.exists()]
        size = FORMAT_SIZES.get(format_name, DEFAULT_SIZE)
        if existing_references:
            generation_prompt = self._reference_generation_prompt(prompt, existing_references, discreet)
        else:
            generation_prompt = prompt

        # The selected backend (OpenAI gpt-image-1 or RunPod/Flux) turns the finished
        # prompt + references into image bytes. Reference/no-reference and any provider
        # retry logic lives inside the backend.
        image_bytes = self.backend.generate(
            prompt=generation_prompt,
            reference_paths=existing_references,
            size=size,
        )

        folder_path.mkdir(parents=True, exist_ok=True)
        image_path = folder_path / file_name
        image_path.write_bytes(image_bytes)
        return GeneratedImage(
            path=image_path,
            relative_path=self._display_path(image_path, repository_root),
            file_name=file_name,
            image_bytes=image_bytes,
        )

    def _reference_generation_prompt(
        self, prompt: str, reference_paths: list[Path], discreet: bool = True
    ) -> str:
        reference_names = ", ".join(path.name for path in reference_paths)
        discreet_directive = (
            "\n## Discreet aid (this post - takes precedence)\n"
            "This is a discreet/subtle scene. These rules OVERRIDE any more detailed visibility, "
            "waistband, see-through, or layering description elsewhere in this prompt. Keep the "
            "incontinence product BARELY noticeable: at most a faint waistband edge or soft padded "
            "contour under fully pulled-up clothing - never a bright white patch, never the product "
            "centered or emphasised. Do NOT focus on the crotch, lap, groin, or seat, and do not "
            "frame a seated phone-down-the-lap POV that points at the groin. Prefer a standing, "
            "walking, or full-body / three-quarter / rear everyday composition in which the orthosis "
            "is the visible aid and the brief stays subtle. Keep the tights and the waistband fully "
            "and EVENLY pulled up across the entire band - never pull the front or centre of the "
            "waistband down into a 'smiley' dip while the sides stay up, and never tug clothing down "
            "to expose the product.\n"
            if discreet
            else ""
        )
        return f"""{prompt}

## Reference Handling Rules
Use the attached reference images only for body proportions, orthosis construction, the incontinence product appearance, outfit material, and everyday location realism.
Match the reference body type: normal non-model figure, slightly broader shoulders, lightly strong upper body, flat narrow chest, natural proportions, no exaggerated waist.
Match the reference hair when visible: dark blond, smooth, strictly pulled back with a clear open forehead and NO fringe / NO bangs (kein Pony). Wear it tied back as a high ponytail (default), a neat bun, or a braid - but use exactly ONE of those hairstyles across every slide of this post (one series = one hairstyle); never mix them within a carousel.
Match the reference outfit family: black polo or black fitted top, black shorts, black tights or leggings, white orthopedic shoes when shoes are visible.
Match the reference aid exactly: the orthosis is always worn on the person's anatomical LEFT leg (the other leg has no orthosis). This depends on orientation, NOT on a fixed image side: in a rear/back view the braced left leg appears on the image-left, in a front view it appears on the image-right, in a side view follow the body. Keep it on the SAME left leg in every slide - never switch legs between slides. It is a Bauerfeind-like knee orthosis with side joints, broad velcro straps, and credible medical proportions, with a clearly VISIBLE blue knit/padded section at the knee (Bauerfeind blue, most visible from the front/side; the hinges, struts and straps stay black) so it stands out against the black tights - never render it all-black and hidden.
If an incontinence product is visible in the scene, reproduce the attached TENA reference 1:1: a white TENA Slip tab brief with a matte textile-nonwoven surface, side refastenable Klettlaschen tabs, a visible central absorbent core (Saugkern), pastel green/blue marking stripes, and a fairly high elastic waistband that sits high on the hips. It must read as this exact adult incontinence brief, never a baby diaper, sporty pull-up, or fantasy brand.
Critical layering: the brief is worn UNDERNEATH the outer clothing (under shorts and/or tights), NEVER pulled on over the trousers. Do not render the diaper as outerwear. Normally only the waistband edge peeks slightly above the tights/shorts band, plus the soft padded contour ("bulge") under the fabric. With shorts plus tights, show only that waistband and contour. With sheer tights and no shorts, the white product may faintly shimmer through the tights while the waistband shows at the top.
The view of the waistband is created naturally via the SHIRT - a shorter shirt, a shirt ridden up on one side or overall, or the person lifting the hem slightly. NEVER reveal it by pulling the trousers/tights down in the middle into a "smiley" waistband shape.
Waistband layering has two cases (the brief/outfit says which): (A) tights waistband HIGHER than the diaper waistband - the tights band sits on top and the diaper band is just below it, showing through the tights; or (B) tights waistband LOWER than the diaper waistband - the white diaper waistband sticks up directly above the tights band and is fully visible there (not through fabric), with the tights band below it. Through tights, how much of the rest shows depends on the denier given in the outfit: the diaper's colour and pattern disappear from roughly 60-80 DEN, but its extra thickness/contour (bulge) stays partly visible even at high denier. Keep it normalized and non-sexualized; show it only as far as the scene's aid-visibility calls for.
Do not copy any text, stickers, layout bars, captions, logos, or graphic design elements from references.
Do not render any words, letters, icons, signatures, app UI, watermarks, labels, badges, or graphic overlays inside the photo.
Do not preserve a visible face from references. The generated person must have the face hidden, cropped out, turned away, or outside the frame.
Do not average all references into a collage. Produce one natural documentary-style Instagram image.
Place the main motif on the right or lower-right third and keep clean negative space on the left/top-left for deterministic overlay text.
{discreet_directive}

## Non-sexual framing (mandatory)
This is matter-of-fact disability and everyday-life documentary content - NOT intimate, boudoir, or lingerie-fashion imagery. Show the person fully dressed in an ordinary situation with clear everyday context in frame (a room, an activity, normal daylight). Do NOT produce an isolated close-up of the buttocks, hips, crotch or underwear, and do not center or emphasise those areas. No fetish or lingerie aesthetic, no suggestive pose, no sheer-bodysuit look. The incontinence product and the orthosis are ordinary medical aids, shown calmly and incidentally - never as the focal subject of a body-part crop. Prefer standing, walking or sitting full-body or three-quarter framing over tight lower-body shots; keep the composition tasteful and clinical-normal.
Attached generation references: {reference_names}
"""

    def _slide_prompt(self, prompt: str, slide_number: int, discreet: bool = True) -> str:
        if slide_number == 2:
            if discreet:
                direction = (
                    "Create a distinct second carousel base photo: a standing or walking everyday moment "
                    "(platform, street, room, doorway), full-body or three-quarter from the side or rear, "
                    "legs and left-leg orthosis visible, relaxed and airy. Do NOT use a seated lap/crotch "
                    "POV or a phone-down-the-lap angle. Keep the main motif in the lower-right half and "
                    "left/top-left calm and empty for overlay."
                )
            else:
                direction = (
                    "Create a distinct second carousel base photo: selfie-from-above or seated POV, "
                    "legs and left-leg orthosis visible, relaxed everyday moment, airy composition, "
                    "main motif in the lower-right half, left/top-left kept calm and empty for overlay."
                )
        elif slide_number == 3:
            direction = (
                "Create a distinct third carousel base photo: mirror selfie or side/rear documentary angle, "
                "outfit and aid visible as everyday context, less dense than slide one, "
                "main motif on the right third with clean space for overlay text."
            )
        else:
            direction = (
                "Create a distinct fourth carousel closing photo: warm everyday documentary image with the person, "
                "not a blank graphic page, usable as a follow/CTA ending. Keep the orthosis on the person's left leg "
                "(same leg as the other slides), keep face hidden, and leave enough calm area for a follow graphic."
            )
        creator_slide = _creator_slide_direction(prompt, slide_number)
        return f"""{prompt}

## Slide Variation
{direction}
{creator_slide}
This must not repeat the exact same pose, crop, room angle, or body placement as another slide.
Generate a clean base photo only: no text, no icons, no labels, no signature, no logo, no graphic overlay.
"""

    def _display_path(self, path: Path, repository_root: Path | None) -> str:
        if repository_root is not None:
            try:
                return path.relative_to(repository_root).as_posix()
            except ValueError:
                pass
        return path.as_posix()


_PROMPT_SCAFFOLD_PREFIXES = (
    "create ", "scene:", "location:", "outfit:", "format", "no ", "do not",
    "aid visibility", "metaphor direction", "generation goal", "hook:", "text:",
    "visual:", "required", "not allowed", "preferred", "allowed", "style:", "layout",
    "match the", "use the", "place the", "keep ", "maximal", "minimal",
)


def _first_prompt_line(prompt: str, fallback: str) -> str:
    for line in prompt.splitlines():
        cleaned = line.strip("- #")
        if (
            cleaned
            and len(cleaned) > 18
            and not cleaned.lower().startswith(_PROMPT_SCAFFOLD_PREFIXES)
        ):
            return cleaned[:80]
    return fallback


def _highlight_line(prompt: str, fallback: str) -> str:
    for marker in ("Hook", "Text:", "Metaphor direction:"):
        for line in prompt.splitlines():
            if marker.lower() in line.lower():
                cleaned = line.split(":", 1)[-1].strip()
                if cleaned:
                    return cleaned[:70]
    return fallback


def _creator_slide_direction(prompt: str, slide_number: int) -> str:
    """Extract a creator-supplied slide block when a free story brief was used."""
    marker = f"### Slide {slide_number}"
    if marker not in prompt:
        return ""
    after = prompt.split(marker, 1)[1]
    next_marker = after.find("\n### Slide ")
    return f"Creator slide direction:\n{after[:next_marker] if next_marker >= 0 else after}".strip()


def _layout_contents_from_carousel(carousel: str, topic: str) -> list[LayoutContent]:
    """Build overlay copy from the production/creator carousel.md instead of default phrases.

    Supports the production format (``## Slide N - Label`` with ``Text:`` / ``Visual:`` lines)
    as well as pasted creator contracts. Returns ``[]`` only when no usable slide copy is
    found, so the caller falls back to default phrasing rather than leaking prompt scaffolding.
    """
    matches = list(re.finditer(r"^##\s+Slide\s+(\d+)\b.*$", carousel, flags=re.MULTILINE))
    if not matches:
        return []
    blocks: list[tuple[int, str]] = []
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(carousel)
        block = carousel[match.end():end]
        # Drop a trailing non-slide heading attached to the last block (e.g. "## Design Guardrails").
        cut = block.find("\n## ")
        if cut >= 0:
            block = block[:cut]
        block = block.strip()
        if block:
            blocks.append((int(match.group(1)), block))
    if not blocks:
        return []

    usable = blocks[:4]
    contents: list[LayoutContent] = []
    for index, (_number, block) in enumerate(usable):
        lines = [line.strip(" -\t") for line in block.splitlines() if line.strip()]
        text = _first_matching_line(lines, "Text:") or _first_matching_line(lines, "Headline:")
        if not text:
            prose = [
                line for line in lines
                if not line.lower().startswith(("visual:", "format", "design", "#"))
            ]
            text = prose[0] if prose else (topic or "Anders gedacht")
        is_last = index == len(usable) - 1
        kind = "hook" if index == 0 else ("cta" if is_last else "detail")
        if kind == "cta":
            contents.append(
                LayoutContent(
                    series_label="Perspective",
                    headline="Folge mir",
                    highlight="für ehrliche Einblicke",
                    body_text=text[:180],
                    icon_labels=("Echt.", "Mutmachend.", "Anders."),
                    slide_number=index + 1,
                    slide_count=4,
                    slide_kind="cta",
                )
            )
        else:
            contents.append(
                LayoutContent(
                    series_label=topic or "Anders gedacht",
                    headline=text[:90],
                    highlight="",
                    icon_labels=("Alltag", "Komfort", "Freiheit"),
                    slide_number=index + 1,
                    slide_count=4,
                    slide_kind=kind,
                )
            )

    while len(contents) < 4:
        index = len(contents)
        is_last = index == 3
        contents.append(
            LayoutContent(
                series_label="Perspective" if is_last else (topic or "Anders gedacht"),
                headline="Folge mir" if is_last else "Anders gedacht",
                highlight="für ehrliche Einblicke" if is_last else "",
                icon_labels=("Echt.", "Mutmachend.", "Anders.") if is_last else ("Alltag", "Komfort", "Freiheit"),
                slide_number=index + 1,
                slide_count=4,
                slide_kind="cta" if is_last else "detail",
            )
        )
    return contents


def _first_matching_line(lines: list[str], marker: str) -> str:
    for line in lines:
        if line.lower().startswith(marker.lower()):
            return line.split(":", 1)[1].strip()
    return ""


def _next_matching_line(lines: list[str], marker: str) -> str:
    for index, line in enumerate(lines):
        if line.lower().startswith(marker.lower()) and index + 1 < len(lines):
            return lines[index + 1]
    return ""
