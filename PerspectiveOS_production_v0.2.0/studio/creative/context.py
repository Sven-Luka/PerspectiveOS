from dataclasses import dataclass

try:
    from ..brain.index import IndexedKnowledge
    from ..core.knowledge import blockquotes, bullets, first_sentence
    from .brief_generator import TOPIC_PROFILES
except ImportError:
    from brain.index import IndexedKnowledge
    from core.knowledge import blockquotes, bullets, first_sentence
    from creative.brief_generator import TOPIC_PROFILES


@dataclass(frozen=True)
class CreativeInputs:
    """Input values used by Perspective Studio creative engines."""

    topic: str
    target_emotion: str
    image_type: str
    location: str = ""
    outfit: str = ""
    aid_visibility: str = "subtle"
    metaphor: str = ""
    format_name: str = "Feed 4:5"


@dataclass(frozen=True)
class CreativeContext:
    """Resolved repository knowledge and user inputs for deterministic generation."""

    topic: str
    target_emotion: str
    image_type: str
    location: str
    outfit: str
    aid_visibility: str
    metaphor: str
    format_name: str
    scene: str
    hook: str
    cta: str
    message_focus: str
    perspective_sentence: str
    metaphor_line: str
    tone: str
    favorite_words: str
    avoid: str
    format_rules: str
    layout_rules: str
    photo_perspectives: str
    character_base: str
    persona_rules: str
    orthosis_rules: str
    incontinence_rules: str


class CreativeContextBuilder:
    """Builds reusable creative context from KnowledgeIndex and Studio inputs."""

    def __init__(self, knowledge: IndexedKnowledge) -> None:
        """Create a context builder for the current repository knowledge index."""
        self.knowledge = knowledge

    def build(self, inputs: CreativeInputs) -> CreativeContext:
        """Resolve repository knowledge and user inputs into one creative context."""
        profile = TOPIC_PROFILES[inputs.topic]
        creator = self.knowledge.document("creative/CreatorBible.md")
        language = self.knowledge.document("creative/LanguageBible.md")
        metaphor_library = self.knowledge.document("creative/MetaphorLibrary.md")
        design = self.knowledge.document("visual/DesignSystem.md")
        photo = self.knowledge.document("visual/PhotoStyle.md")
        character = self.knowledge.document("persona/Character.md")
        incontinence = self.knowledge.document("persona/Incontinence.md")
        orthosis = self.knowledge.document("persona/Orthosis.md")
        outfit_doc = self.knowledge.document("persona/OutfitGuide.md")

        selected_metaphor = inputs.metaphor.strip() or profile.metaphor
        location = inputs.location.strip() or _first_or_default(
            bullets(photo, "Orte"),
            "a natural everyday location",
        )
        outfit = inputs.outfit.strip() or _first_or_default(
            bullets(outfit_doc, "Bevorzugt"),
            "modern everyday clothing",
        )

        return CreativeContext(
            topic=inputs.topic,
            target_emotion=inputs.target_emotion,
            image_type=inputs.image_type,
            location=location,
            outfit=outfit,
            aid_visibility=inputs.aid_visibility,
            metaphor=selected_metaphor,
            format_name=inputs.format_name,
            scene=f"{profile.scene} at {location} with {outfit}",
            hook=profile.hook,
            cta=profile.cta,
            message_focus=profile.message_focus,
            perspective_sentence=_first_quote(
                creator,
                "Der Perspective Moment",
                profile.message_focus.capitalize(),
            ),
            metaphor_line=_metaphor_for_topic(metaphor_library, selected_metaphor),
            tone=_join_or_default(
                bullets(language, "Ton"),
                "warm, freundlich, modern, selbstironisch, klar",
            ),
            favorite_words=_join_or_default(
                bullets(language, "Lieblingswoerter"),
                "sichtbar, Alltag, unterwegs, Perspektive, Freiheit, Outfit",
            ),
            avoid=_join_or_default(
                bullets(language, "Woerter vermeiden"),
                "Mitleid, Schock, Fetischisierung, Heldengeschichte",
            ),
            format_rules=_join_or_default(bullets(design, "Format"), "1080 x 1350 px, 4:5"),
            layout_rules=_join_or_default(bullets(design, "Layout"), "viel Bild, wenig Text"),
            photo_perspectives=_join_or_default(
                bullets(photo, "Bevorzugte Perspektiven"),
                "Selfie von oben, POV, Spiegelaufnahme ohne Gesicht, von hinten beim Gehen",
            ),
            character_base=first_sentence(
                character,
                "Die Figur wirkt wie eine reale Person im Alltag.",
            ),
            persona_rules=_join_or_default(
                bullets(character, "Haltung"),
                "self-aware, natural, not model-like, not oversexualized",
            ),
            orthosis_rules=_join_or_default(
                bullets(orthosis, "Pflicht"),
                "Orthese am linken Bein",
            ),
            incontinence_rules=_join_or_default(
                bullets(incontinence, "Sichtbarkeit"),
                "alltagsbezogene Sichtbarkeit ohne sexualisierte Darstellung",
            ),
        )


def _first_or_default(values: list[str], fallback: str) -> str:
    return values[0] if values else fallback


def _first_quote(content: str, heading: str, fallback: str) -> str:
    quotes = blockquotes(content, heading)
    return quotes[0] if quotes else fallback


def _join_or_default(values: list[str], fallback: str) -> str:
    return ", ".join(values) if values else fallback


def _metaphor_for_topic(content: str, metaphor: str) -> str:
    marker = f"## {metaphor}"
    if marker not in content:
        return f"{metaphor} as an everyday comparison that makes the perspective easier to understand."

    after_marker = content.split(marker, 1)[1]
    next_heading = after_marker.find("\n## ")
    metaphor_section = after_marker[:next_heading] if next_heading != -1 else after_marker
    quotes = blockquotes(metaphor_section)
    if quotes:
        return quotes[0]

    lines = [line.strip() for line in metaphor_section.splitlines() if line.strip()]
    return lines[0] if lines else f"{metaphor} as a practical everyday comparison."
