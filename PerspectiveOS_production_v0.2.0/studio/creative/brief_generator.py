from dataclasses import dataclass

from brain.index import IndexedKnowledge
from core.knowledge import blockquotes, bullets, first_sentence


@dataclass(frozen=True)
class TopicProfile:
    """Creative defaults for a supported Perspective Studio topic."""

    message_focus: str
    scene: str
    metaphor: str
    hook: str
    cta: str


class BriefGenerator:
    """Creates deterministic production briefs from indexed repository knowledge."""

    def __init__(self, knowledge: IndexedKnowledge) -> None:
        """Create a brief generator bound to a repository knowledge index."""
        self.knowledge = knowledge

    def generate(self, topic: str, target_emotion: str, image_type: str) -> str:
        """Generate a production brief for a topic, target emotion, and image type."""
        profile = TOPIC_PROFILES[topic]
        creator = self.knowledge.document("creative/CreatorBible.md")
        language = self.knowledge.document("creative/LanguageBible.md")
        metaphor_library = self.knowledge.document("creative/MetaphorLibrary.md")
        design = self.knowledge.document("visual/DesignSystem.md")
        photo = self.knowledge.document("visual/PhotoStyle.md")
        character = self.knowledge.document("persona/Character.md")
        incontinence = self.knowledge.document("persona/Incontinence.md")
        orthosis = self.knowledge.document("persona/Orthosis.md")
        outfit = self.knowledge.document("persona/OutfitGuide.md")

        core_rule = _first_quote(
            creator,
            "Grundregel",
            "Lifestyle fuehrt. Hilfsmittel begleiten.",
        )
        tone = _join_or_default(
            bullets(language, "Ton"),
            "warm, freundlich, modern, selbstironisch, klar",
        )
        favorite_words = _join_or_default(
            bullets(language, "Lieblingswoerter"),
            "sichtbar, Alltag, unterwegs, Perspektive, Freiheit, Outfit",
        )
        avoid = _join_or_default(
            bullets(language, "Woerter vermeiden"),
            "Mitleid, Schock, Fetischisierung, Heldengeschichte",
        )
        metaphor_line = _metaphor_for_topic(metaphor_library, profile.metaphor)
        format_rules = _join_or_default(bullets(design, "Format"), "1080 x 1350 px, 4:5")
        layout_rules = _join_or_default(bullets(design, "Layout"), "viel Bild, wenig Text")
        photo_places = _join_or_default(
            bullets(photo, "Orte"),
            "Zug, Bahnhof, Cafe, Supermarkt, Wohnung",
        )
        photo_perspectives = _join_or_default(
            bullets(photo, "Bevorzugte Perspektiven"),
            "Selfie von oben, POV, Spiegelaufnahme ohne Gesicht, von hinten beim Gehen",
        )
        character_base = first_sentence(
            character,
            "Die Figur wirkt wie eine reale Person im Alltag.",
        )
        outfit_base = first_sentence(outfit, "Kleidung ist Ausdruck, keine Tarnung.")
        orthosis_rules = _join_or_default(
            bullets(orthosis, "Pflicht"),
            "Orthese am linken Bein",
        )
        incontinence_rules = _join_or_default(
            bullets(incontinence, "Sichtbarkeit"),
            "alltagsbezogene Sichtbarkeit ohne sexualisierte Darstellung",
        )

        message = (
            f"{profile.message_focus.capitalize()}. The brief follows the repository rule "
            f"'{core_rule}' with target emotion: {target_emotion}."
        )
        visual_idea = (
            f"{profile.scene}. {IMAGE_TYPE_GUIDANCE[image_type]} "
            f"Use {photo_perspectives}. Possible locations: {photo_places}."
        )
        caption = _caption(profile, target_emotion, tone, metaphor_line)
        image_prompt = _image_prompt(
            profile,
            image_type,
            format_rules,
            layout_rules,
            character_base,
            outfit_base,
            orthosis_rules,
            incontinence_rules,
        )
        video_prompt = _video_prompt(profile, target_emotion, image_type, photo_perspectives)

        return f"""# Production Brief

## Topic
{topic}

## Message
{message}

## Visual Idea
{visual_idea}

## Hook
{profile.hook}

## Caption
{caption}

## Hashtags
#PerspectiveOS #Sichtbarkeit #Alltag #Outfit #Perspektivwechsel

## CTA
{profile.cta}

## Comment Strategy
Answer with {tone}. Shift attention from judgement to Alltag, use favorite language such as {favorite_words}, and avoid {avoid}. Keep boundaries clear: this account shows everyday life, not fantasy.

## Image Prompt
{image_prompt}

## Video Prompt
{video_prompt}
"""


TOPIC_PROFILES = {
    "Anders gedacht": TopicProfile(
        message_focus="turn a quick judgement into a warmer everyday perspective",
        scene="a casual moment unterwegs where the outfit, posture, and assistive devices are visible as part of daily life",
        metaphor="Brille",
        hook="Was, wenn das nicht auffallen soll, sondern einfach dazugehort?",
        cta="Welche Perspektive hat sich bei dir erst im Alltag verandert?",
    ),
    "Outfit": TopicProfile(
        message_focus="show clothing as expression rather than camouflage",
        scene="a mirror or street-style image with shorts, tights or leggings, sneakers, and a confident everyday outfit",
        metaphor="Sneaker",
        hook="Ich ziehe mich nicht an, damit andere weniger sehen.",
        cta="Welches Kleidungsstuck tragt bei dir am meisten Selbstvertrauen?",
    ),
    "Orthosis": TopicProfile(
        message_focus="make the orthosis understandable as mobility support without making it the whole identity",
        scene="a walking, stair, train, or shopping scene where the left-leg orthosis is visible but not staged as the only subject",
        metaphor="Fahrradhelm",
        hook="Man sieht die Orthese. Man vergisst nur manchmal, warum sie da ist.",
        cta="Welche Alltagshilfe wird deiner Meinung nach noch zu oft falsch gelesen?",
    ),
    "Incontinence": TopicProfile(
        message_focus="normalize incontinence products as practical aids without shame or sensationalism",
        scene="packing a bag, choosing an outfit, or moving through a normal day with discreet, practical product visibility",
        metaphor="Regenschirm",
        hook="Gut vorbereitet ist nicht peinlich. Es ist Alltag.",
        cta="Was packst du ein, damit dein Tag entspannter wird?",
    ),
    "Dating": TopicProfile(
        message_focus="shift attention from visible aids back to the whole person",
        scene="a cafe, street, or mirror-before-leaving moment with warm styling and a clear sense of personality",
        metaphor="Tattoo",
        hook="Wenn du nur das Hilfsmittel siehst, verpasst du den Menschen.",
        cta="Was sollte ein erstes Date deiner Meinung nach wirklich sehen?",
    ),
    "Humor": TopicProfile(
        message_focus="use warm self-irony to soften assumptions without making disability the joke",
        scene="a small everyday mishap with clothing, coffee, a bag, tights, or velcro",
        metaphor="Powerbank",
        hook="Mein Outfit hatte einen Plan. Der Klettverschluss auch.",
        cta="Welche kleine Alltagspanne verdient mehr Humor?",
    ),
    "Community": TopicProfile(
        message_focus="invite respectful conversation while keeping clear personal boundaries",
        scene="a calm everyday image that feels open, warm, and easy to respond to",
        metaphor="Brille",
        hook="Nicht alles, was sichtbar ist, ist eine Einladung zur Bewertung.",
        cta="Welche Frage wurde dir schon einmal respektvoll gestellt?",
    ),
}

EMOTION_GUIDANCE = {
    "Smile": "Keep the tone warm, light, and self-ironic.",
    "Think": "Build toward a clear perspective shift that lingers after reading.",
    "Empower": "Emphasize agency, clothing as expression, and visible everyday confidence.",
    "Surprise": "Start from a familiar assumption and gently reverse it.",
}

IMAGE_TYPE_GUIDANCE = {
    "Single Image": "Use one strong 4:5 image with a clear hook and generous negative space.",
    "Carousel": "Use four slides: hook, reality moment, metaphor or perspective shift, warm ending with community question.",
    "Reel": "Use a short sequence with a natural opening, one everyday movement, one perspective sentence, and a warm final frame.",
}


def _caption(
    profile: TopicProfile,
    target_emotion: str,
    tone: str,
    metaphor_line: str,
) -> str:
    guidance = EMOTION_GUIDANCE[target_emotion]
    return (
        f"Begin with a small everyday scene: {profile.scene}. "
        f"Add a concise observation in a {tone} tone. "
        f"Use the metaphor '{profile.metaphor}': {metaphor_line}. "
        f"{guidance} End with: {profile.cta}"
    )


def _image_prompt(
    profile: TopicProfile,
    image_type: str,
    format_rules: str,
    layout_rules: str,
    character_base: str,
    outfit_base: str,
    orthosis_rules: str,
    incontinence_rules: str,
) -> str:
    return (
        f"Create a natural Perspective OS {image_type.lower()} visual. "
        f"Scene: {profile.scene}. "
        f"Format and composition: {format_rules}. Layout: {layout_rules}. "
        f"Character: {character_base} Face should not be the focus. "
        f"Outfit principle: {outfit_base} "
        f"Orthosis consistency: {orthosis_rules}. "
        f"Incontinence boundary: {incontinence_rules}. "
        "The person leads, assistive devices accompany. No pity framing, no shock image, no fetishized or voyeuristic angle."
    )


def _video_prompt(
    profile: TopicProfile,
    target_emotion: str,
    image_type: str,
    photo_perspectives: str,
) -> str:
    if image_type != "Reel":
        return (
            "Optional motion version: start with the everyday scene, show one small movement, "
            f"bring in the {profile.metaphor} perspective, and end with the CTA. "
            f"Emotional direction: {target_emotion.lower()}."
        )

    return (
        f"Reel structure: open on {profile.scene}; cut to a natural detail using {photo_perspectives}; "
        f"overlay the hook '{profile.hook}'; add the {profile.metaphor} perspective; "
        f"close with '{profile.cta}'. Keep motion casual, documentary, and respectful."
    )


def _first_quote(content: str, heading: str, fallback: str) -> str:
    quotes = blockquotes(content, heading)
    return quotes[0] if quotes else fallback


def _join_or_default(values: list[str], fallback: str) -> str:
    return ", ".join(values) if values else fallback


def _metaphor_for_topic(content: str, metaphor: str) -> str:
    marker = f"## {metaphor}"
    if marker not in content:
        return f"{metaphor} as an everyday object that makes life easier without needing to be hidden."

    after_marker = content.split(marker, 1)[1]
    next_heading = after_marker.find("\n## ")
    metaphor_section = after_marker[:next_heading] if next_heading != -1 else after_marker
    quotes = blockquotes(metaphor_section)
    if quotes:
        return quotes[0]

    lines = [line.strip() for line in metaphor_section.splitlines() if line.strip()]
    return lines[0] if lines else f"{metaphor} as a practical everyday comparison."
