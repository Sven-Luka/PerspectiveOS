import base64
from dataclasses import dataclass
from pathlib import Path
import re

try:
    from ..brain.index import IndexedKnowledge
    from ..core.settings import ProjectSettings
except ImportError:
    from brain.index import IndexedKnowledge
    from core.settings import ProjectSettings

from .generator import DEFAULT_SIZE, FORMAT_SIZES, GeneratedImage, ImageGenerationError, ImageGenerator
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
        self.generator = ImageGenerator(api_key)
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

        image = self._generate_image(
            prompt=prompt,
            reference_paths=[reference.path for reference in self._generation_references(references)],
            folder_path=folder_path,
            format_name=format_name,
            repository_root=repository_root,
            file_name="image.png",
        )
        base_images = [image]
        for slide_number in (2, 3, 4):
            base_images.append(
                self._generate_image(
                    prompt=self._slide_prompt(prompt, slide_number),
                    reference_paths=[reference.path for reference in self._generation_references(references)],
                    folder_path=folder_path,
                    format_name=format_name,
                    repository_root=repository_root,
                    file_name=f"image_slide_{slide_number:02d}.png",
                )
            )
        contract = self.contract_builder.build()
        carousel_layouts = self._compose_carousel_layouts(
            image_paths=[base_image.path for base_image in base_images],
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
    ) -> list[ComposedLayout]:
        custom_contents = _layout_contents_from_carousel(carousel_content, topic)
        if custom_contents:
            return self.composer.compose_carousel(
                source_images=image_paths,
                folder_path=folder_path,
                contents=custom_contents,
                repository_root=repository_root,
            )
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
        return self.composer.compose_carousel(
            source_images=image_paths,
            folder_path=folder_path,
            contents=contents,
            repository_root=repository_root,
        )

    def _generation_references(self, references: list[ReferenceImage]) -> list[ReferenceImage]:
        """Return the focused subset of references that should be attached to image generation."""
        selected: list[ReferenceImage] = []
        seen_paths: set[str] = set()
        seen_ids: set[str] = set()
        preferred_prefixes = (
            "character/body_silhouette",
            "orthosis/front",
            "orthosis/side",
            "locations/",
            "outfits/",
            "diapers/",
        )
        blocked_prefixes = (
            "layouts/",
            "rejected/",
            "orthosis/details",
            "diapers/details_closeup",
        )

        for prefix in preferred_prefixes:
            for reference in references:
                if len(selected) >= 4:
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
    ) -> GeneratedImage:
        existing_references = [path for path in reference_paths if path.exists()]
        if not existing_references:
            return self.generator.generate(
                prompt=prompt,
                folder_path=folder_path,
                format_name=format_name,
                repository_root=repository_root,
                file_name=file_name,
            )

        try:
            from openai import OpenAI
        except ImportError as exc:  # pragma: no cover - dependency hint
            raise ImageGenerationError(
                "The 'openai' package is not installed. Run: pip install -r requirements.txt"
            ) from exc

        client = OpenAI(api_key=self.api_key)
        size = FORMAT_SIZES.get(format_name, DEFAULT_SIZE)
        generation_prompt = self._reference_generation_prompt(prompt, existing_references)
        handles = [path.open("rb") for path in existing_references]
        try:
            result = client.images.edit(
                model=self.generator.model,
                image=handles,
                prompt=generation_prompt,
                size=size,
                quality="high",
                n=1,
            )
        except TypeError as exc:
            raise ImageGenerationError(
                "Reference-guided image generation is not supported by the installed OpenAI SDK. "
                "Update dependencies with: pip install -r requirements.txt"
            ) from exc
        except Exception as exc:
            raise ImageGenerationError(f"Reference-guided image generation failed: {exc}") from exc
        finally:
            for handle in handles:
                handle.close()

        image_bytes = base64.b64decode(result.data[0].b64_json)
        folder_path.mkdir(parents=True, exist_ok=True)
        image_path = folder_path / file_name
        image_path.write_bytes(image_bytes)

        return GeneratedImage(
            path=image_path,
            relative_path=self._display_path(image_path, repository_root),
            file_name=file_name,
            image_bytes=image_bytes,
        )

    def _reference_generation_prompt(self, prompt: str, reference_paths: list[Path]) -> str:
        reference_names = ", ".join(path.name for path in reference_paths)
        return f"""{prompt}

## Reference Handling Rules
Use the attached reference images only for body proportions, orthosis construction, outfit material, and everyday location realism.
Match the reference body type: normal non-model figure, slightly broader shoulders, lightly strong upper body, flat narrow chest, natural proportions, no exaggerated waist.
Match the reference hair when visible: dark blond, smooth, high ponytail, everyday movement, not overly styled, not too long.
Match the reference outfit family: black polo or black fitted top, black shorts, black tights or leggings, white orthopedic shoes when shoes are visible.
Match the reference aid exactly: in the final camera/viewer direction the orthosis must be on the LEFT side of the image. It is a black/dark-blue Bauerfeind-like knee orthosis with side joints, broad velcro straps, and credible medical proportions. The other leg has no orthosis. Never move the orthosis to the right side of the image.
Do not copy any text, stickers, layout bars, captions, logos, or graphic design elements from references.
Do not render any words, letters, icons, signatures, app UI, watermarks, labels, badges, or graphic overlays inside the photo.
Do not preserve a visible face from references. The generated person must have the face hidden, cropped out, turned away, or outside the frame.
Do not average all references into a collage. Produce one natural documentary-style Instagram image.
Place the main motif on the right or lower-right third and keep clean negative space on the left/top-left for deterministic overlay text.
Attached generation references: {reference_names}
"""

    def _slide_prompt(self, prompt: str, slide_number: int) -> str:
        if slide_number == 2:
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
                "not a blank graphic page, usable as a follow/CTA ending. Keep the orthosis on the left side of the image "
                "from the viewer's direction, keep face hidden, and leave enough calm area for a follow graphic."
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


def _first_prompt_line(prompt: str, fallback: str) -> str:
    for line in prompt.splitlines():
        cleaned = line.strip("- #")
        if cleaned and len(cleaned) > 18 and not cleaned.lower().startswith(
            ("create ", "scene:", "location:", "outfit:", "format", "no ", "do not")
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
    """Build overlay copy from a pasted creator carousel instead of fixed default phrases."""
    if "## Creator Story Contract" not in carousel:
        return []
    matches = list(re.finditer(r"^## Slide (\d+)\s*$", carousel, flags=re.MULTILINE))
    if not matches:
        return []
    blocks: list[tuple[int, str]] = []
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(carousel)
        blocks.append((int(match.group(1)), carousel[match.end():end].strip()))

    count = max(4, len(blocks))
    contents: list[LayoutContent] = []
    for index, (number, block) in enumerate(blocks[:4]):
        lines = [line.strip(" -\t") for line in block.splitlines()]
        prose = [line for line in lines if line and not line.startswith("#") and not line.endswith(":")]
        headline = _first_matching_line(lines, "Headline:") or (prose[0] if prose else "Anders gedacht")
        highlight = _next_matching_line(lines, "Text:") or (prose[1] if len(prose) > 1 else "ehrlich. alltagstauglich. anders.")
        kind = "cta" if index == min(3, len(blocks) - 1) else ("hook" if index == 0 else "detail")
        contents.append(
            LayoutContent(
                series_label=topic or "Anders gedacht",
                headline=headline[:90],
                highlight=highlight[:80],
                body_text=" ".join(prose[2:5])[:180],
                icon_labels=("Alltag", "Komfort", "Freiheit") if kind != "cta" else ("Echt.", "Mutmachend.", "Anders."),
                slide_number=index + 1,
                slide_count=count,
                slide_kind=kind,
            )
        )

    while len(contents) < 4:
        index = len(contents)
        contents.append(
            LayoutContent(
                series_label="Perspective",
                headline="Folge mir" if index == 3 else "Anders gedacht",
                highlight="fuer ehrliche Einblicke",
                icon_labels=("Echt.", "Mutmachend.", "Anders."),
                slide_number=index + 1,
                slide_count=4,
                slide_kind="cta" if index == 3 else "detail",
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
