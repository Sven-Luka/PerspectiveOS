from dataclasses import dataclass

try:
    from ..brain.index import IndexedKnowledge
    from ..core.knowledge import bullets
except ImportError:
    from brain.index import IndexedKnowledge
    from core.knowledge import bullets


@dataclass(frozen=True)
class ImagePromptContract:
    """Resolved non-negotiable image rules used before image generation."""

    master_prompt: str
    character_body: list[str]
    character_hair: list[str]
    character_face: list[str]
    character_pose: list[str]
    orthosis_required: list[str]
    orthosis_forbidden: list[str]
    design_format: list[str]
    design_style: list[str]
    design_layout: list[str]
    design_text_rules: list[str]
    carousel_standard: str
    carousel_rule: str
    photo_perspectives: list[str]
    photo_locations: list[str]

    @property
    def required_terms(self) -> tuple[str, ...]:
        return (
            "normale Figur",
            "breitere Schultern",
            "flache",
            "androgyne Silhouette",
            "dunkelblond",
            "hoher Pferdeschwanz",
            "Gesicht nicht sichtbar",
            "linken Bein",
            "von vorne betrachtet",
            "links im Bild",
            "seitliche Gelenke",
            "breite Klettgurte",
            "1080",
            "1350",
            "4:5",
            "Sicherheitsrand",
            "90 px",
            "viel Bild",
            "wenig Text",
            "keine 4-Panel-Collagen",
        )


class ImagePromptContractBuilder:
    """Builds a deterministic image prompt contract from repository source documents."""

    def __init__(self, knowledge: IndexedKnowledge) -> None:
        self.knowledge = knowledge

    def build(self) -> ImagePromptContract:
        character = self.knowledge.document("persona/Character.md")
        orthosis = self.knowledge.document("persona/Orthosis.md")
        design = self.knowledge.document("visual/DesignSystem.md")
        carousel = self.knowledge.document("visual/CarouselSystem.md")
        photo = self.knowledge.document("visual/PhotoStyle.md")

        return ImagePromptContract(
            master_prompt=self.knowledge.document("prompts/image/master_image_prompt.md").strip(),
            character_body=bullets(character, "Körper") or bullets(character, "Koerper"),
            character_hair=bullets(character, "Haare"),
            character_face=bullets(character, "Gesicht"),
            character_pose=bullets(character, "Haltung"),
            orthosis_required=bullets(orthosis, "Pflicht"),
            orthosis_forbidden=bullets(orthosis, "Nicht erlaubt"),
            design_format=bullets(design, "Format"),
            design_style=bullets(design, "Stil"),
            design_layout=bullets(design, "Layout"),
            design_text_rules=bullets(design, "Textregeln"),
            carousel_standard=_section_lines(carousel, "Standard"),
            carousel_rule=_section_text(carousel, "Regel"),
            photo_perspectives=bullets(photo, "Bevorzugte Perspektiven"),
            photo_locations=bullets(photo, "Orte"),
        )


def render_image_prompt_contract(
    contract: ImagePromptContract,
    *,
    format_name: str,
    scene: str,
    location: str,
    outfit: str,
    aid_visibility: str,
    metaphor: str,
    metaphor_line: str,
) -> str:
    """Render a generation prompt with explicit hard constraints and source-derived values."""
    return f"""# Image Prompt

## Generation Goal
Create a Perspective OS Instagram visual in {format_name}.

## Scene Brief
Scene: {scene}
Location: {location}
Outfit: {outfit}
Aid visibility: {aid_visibility}
Metaphor direction: {metaphor} - {metaphor_line}

## Hard Character Contract
{_bullet_block(contract.character_body)}

## Hair And Face Contract
Hair:
{_bullet_block(contract.character_hair)}

Face:
{_bullet_block(contract.character_face)}

## Pose And Representation Contract
{_bullet_block(contract.character_pose)}

## Orthosis Contract
Required:
{_bullet_block(contract.orthosis_required)}

Not allowed:
{_bullet_block(contract.orthosis_forbidden)}

## Layout Contract
Format:
{_bullet_block(contract.design_format)}

Style:
{_bullet_block(contract.design_style)}

Layout:
{_bullet_block(contract.design_layout)}

Text rules:
{_bullet_block(contract.design_text_rules)}

Carousel/layout guard:
- {contract.carousel_standard}
- {contract.carousel_rule}

## Photo Contract
Preferred perspectives:
{_bullet_block(contract.photo_perspectives)}

Allowed everyday locations:
{_bullet_block(contract.photo_locations)}

## Master Prompt Source
{contract.master_prompt}

## Non-Negotiable Negative Prompt
No pity framing. No shock image. No fetishized or voyeuristic angle. No fantasy orthosis. No futuristic exoskeleton. No changing orthosis side. No perfect model body. No visible face. No face-focused portrait. No studio aesthetic. No overloaded infographic. No 4-panel collage. Do not copy text, labels, stickers, logos, slogans, UI bars, or graphic layout elements from reference images. No visible image text unless the production brief explicitly supplies exact slide text.

## Final Instruction
Generate a clean base photo only. Prefer selfie-from-above, POV, mirror-with-phone-covering-face, or rear/side documentary perspectives from the Photo Contract. Keep the main person or detail on the right or lower-right third whenever possible and leave calm negative space on the left/top-left for later overlay text. Do not render any words, titles, labels, stickers, UI icons, badges, counters, signatures, branding, or graphic design in the photo itself. The person leads. Lifestyle leads. Assistive devices accompany. If any hard character, orthosis, layout, or safety constraint conflicts with the scene, preserve the contract and simplify the scene.
"""


def missing_required_terms(prompt: str, contract: ImagePromptContract) -> list[str]:
    normalized = prompt.lower()
    return [term for term in contract.required_terms if term.lower() not in normalized]


def _bullet_block(values: list[str]) -> str:
    if not values:
        return "- No source values found."
    return "\n".join(f"- {value}" for value in values)


def _section_text(content: str, heading: str) -> str:
    try:
        from ..core.knowledge import section
    except ImportError:
        from core.knowledge import section
    return " ".join(line.strip() for line in section(content, heading).splitlines() if line.strip())


def _section_lines(content: str, heading: str) -> str:
    return _section_text(content, heading) or "Each carousel image uses a single 1080 x 1350 px frame."
