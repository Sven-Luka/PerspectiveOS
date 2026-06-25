import json
from datetime import datetime

from brain.index import IndexedKnowledge
from core.knowledge import blockquotes, bullets, first_sentence
from creative.brief_generator import BriefGenerator, TOPIC_PROFILES
from .models import ProductionRequest


class ProductionArtifactGenerator:
    """Generates deterministic production artifacts from a request and repository knowledge."""

    def __init__(self, knowledge: IndexedKnowledge) -> None:
        """Create an artifact generator bound to the current KnowledgeIndex output."""
        self.knowledge = knowledge

    def generate_all(self, request: ProductionRequest) -> dict[str, str]:
        """Generate every file required for a production folder."""
        context = self._context(request)
        files = {
            "brief.md": self.brief(context, request),
            "caption.md": self.caption(context),
            "carousel.md": self.carousel(context),
            "image_prompt.md": self.image_prompt(context),
            "video_prompt.md": self.video_prompt(context),
            "comments.md": self.comments(context),
            "checklist.md": self.checklist(context),
            "metadata.json": self.metadata(context),
        }
        return files

    def brief(self, context: dict[str, str], request: ProductionRequest) -> str:
        """Generate the main production brief artifact with v0.3 context fields."""
        base_brief = BriefGenerator(self.knowledge).generate(
            request.topic,
            request.target_emotion,
            request.image_type,
        ).strip()
        return f"""{base_brief}

## Production Context
Location: {context["location"]}
Outfit: {context["outfit"]}
Aid visibility: {context["aid_visibility"]}
Metaphor: {context["metaphor"]}
Format: {context["format_name"]}

## Production Folder Notes
Use the companion files in this folder as the operational source for caption, carousel structure, prompts, comments, checklist, and metadata.
"""

    def caption(self, context: dict[str, str]) -> str:
        """Generate the caption artifact."""
        return f"""# Caption

## Opening Scene
{context["scene"]}

## Caption Draft
Heute: {context["location"]}, {context["outfit"]}, und ein Moment, der erst auf den zweiten Blick richtig lesbar wird.

Man kann auf {context["aid_visibility"]} schauen und trotzdem den Menschen sehen.

Wie bei {context["metaphor"]}: Es geht nicht darum, Aufmerksamkeit zu suchen. Es geht darum, den Alltag leichter, freier oder ehrlicher zu machen.

{context["perspective_sentence"]}

## CTA
{context["cta"]}

## Hashtags
#PerspectiveOS #Sichtbarkeit #Alltag #Outfit #Perspektivwechsel
"""

    def carousel(self, context: dict[str, str]) -> str:
        """Generate the carousel structure artifact."""
        return f"""# Carousel

## Format
{context["format_name"]}

## Slide 1 - Hook
Text: {context["hook"]}
Visual: {context["scene"]}

## Slide 2 - Reality
Text: Alltag zuerst. Hilfsmittel begleiten.
Visual: {context["location"]}, natural smartphone look, {context["outfit"]}.

## Slide 3 - Perspective
Text: {context["metaphor_line"]}
Visual: calm detail, enough safe margin, no over-staging.

## Slide 4 - Warm Ending
Text: {context["perspective_sentence"]}
CTA: {context["cta"]}
"""

    def image_prompt(self, context: dict[str, str]) -> str:
        """Generate the image prompt artifact."""
        return f"""# Image Prompt

Create a Perspective OS visual in {context["format_name"]}.

Scene: {context["scene"]}
Location: {context["location"]}
Outfit: {context["outfit"]}
Aid visibility: {context["aid_visibility"]}
Metaphor direction: {context["metaphor"]} - {context["metaphor_line"]}

Character rules: {context["character_base"]}
Orthosis rules: {context["orthosis_rules"]}
Incontinence rules: {context["incontinence_rules"]}
Visual rules: {context["format_rules"]}; {context["layout_rules"]}
Photo style: {context["photo_perspectives"]}

The person leads. Assistive devices accompany. No pity framing, no shock image, no fetishized or voyeuristic angle.
"""

    def video_prompt(self, context: dict[str, str]) -> str:
        """Generate the video prompt artifact."""
        return f"""# Video Prompt

## Structure
1. Open on {context["location"]} with {context["outfit"]}.
2. Show one natural everyday movement.
3. Let {context["aid_visibility"]} be visible only as the context requires.
4. Bring in the {context["metaphor"]} perspective.
5. End with: {context["cta"]}

## Tone
{context["tone"]}

## Final Frame
{context["perspective_sentence"]}
"""

    def comments(self, context: dict[str, str]) -> str:
        """Generate the comment strategy artifact."""
        return f"""# Comment Strategy

## Tone
{context["tone"]}

## Strategy
- Shift attention from judgement to everyday context.
- Keep boundaries clear without sounding aggressive.
- Use warm self-irony when it fits.
- Do not explain the person away through the aid.

## Example Replies
- Jeder darf Dinge unterschiedlich wahrnehmen. Dieser Account zeigt Alltag.
- Eigentlich wollte ich nur {context["location"]} zeigen. Die Perspektive kam mit.
- Nicht alles, was sichtbar ist, ist eine Einladung zur Bewertung.

## Avoid
{context["avoid"]}
"""

    def checklist(self, context: dict[str, str]) -> str:
        """Generate the production checklist artifact."""
        return f"""# Checklist

- [ ] Topic is clear: {context["topic"]}
- [ ] Target emotion is clear: {context["target_emotion"]}
- [ ] Format is correct: {context["format_name"]}
- [ ] Location is usable: {context["location"]}
- [ ] Outfit supports the story: {context["outfit"]}
- [ ] Aid visibility is intentional: {context["aid_visibility"]}
- [ ] Lifestyle leads before assistive devices.
- [ ] The person is shown first.
- [ ] Humor is warm and respectful.
- [ ] No pity, shock, fetish framing, or voyeuristic angle.
- [ ] Text stays light and readable.
- [ ] CTA invites respectful community response.
"""

    def metadata(self, context: dict[str, str]) -> str:
        """Generate the metadata JSON artifact."""
        payload = {
            "version": "0.3",
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "topic": context["topic"],
            "target_emotion": context["target_emotion"],
            "image_type": context["image_type"],
            "location": context["location"],
            "outfit": context["outfit"],
            "aid_visibility": context["aid_visibility"],
            "metaphor": context["metaphor"],
            "format": context["format_name"],
            "knowledge_loaded": self.knowledge.loaded_documents,
            "knowledge_missing": self.knowledge.missing_documents,
        }
        return json.dumps(payload, indent=2, ensure_ascii=False)

    def _context(self, request: ProductionRequest) -> dict[str, str]:
        profile = TOPIC_PROFILES[request.topic]
        creator = self.knowledge.document("creative/CreatorBible.md")
        language = self.knowledge.document("creative/LanguageBible.md")
        metaphor_library = self.knowledge.document("creative/MetaphorLibrary.md")
        design = self.knowledge.document("visual/DesignSystem.md")
        photo = self.knowledge.document("visual/PhotoStyle.md")
        character = self.knowledge.document("persona/Character.md")
        incontinence = self.knowledge.document("persona/Incontinence.md")
        orthosis = self.knowledge.document("persona/Orthosis.md")
        outfit = self.knowledge.document("persona/OutfitGuide.md")

        selected_metaphor = request.metaphor.strip() or profile.metaphor
        location = request.location.strip() or _first_or_default(
            bullets(photo, "Orte"),
            "a natural everyday location",
        )
        selected_outfit = request.outfit.strip() or _first_or_default(
            bullets(outfit, "Bevorzugt"),
            "modern everyday clothing",
        )

        return {
            "topic": request.topic,
            "target_emotion": request.target_emotion,
            "image_type": request.image_type,
            "format_name": request.format_name,
            "location": location,
            "outfit": selected_outfit,
            "aid_visibility": request.aid_visibility,
            "metaphor": selected_metaphor,
            "scene": f"{profile.scene} at {location} with {selected_outfit}",
            "hook": profile.hook,
            "cta": profile.cta,
            "perspective_sentence": _first_quote(
                creator,
                "Der Perspective Moment",
                profile.message_focus.capitalize(),
            ),
            "metaphor_line": _metaphor_for_topic(metaphor_library, selected_metaphor),
            "tone": _join_or_default(
                bullets(language, "Ton"),
                "warm, freundlich, modern, selbstironisch, klar",
            ),
            "avoid": _join_or_default(
                bullets(language, "Woerter vermeiden"),
                "Mitleid, Schock, Fetischisierung, Heldengeschichte",
            ),
            "format_rules": _join_or_default(bullets(design, "Format"), "1080 x 1350 px, 4:5"),
            "layout_rules": _join_or_default(bullets(design, "Layout"), "viel Bild, wenig Text"),
            "photo_perspectives": _join_or_default(
                bullets(photo, "Bevorzugte Perspektiven"),
                "Selfie von oben, POV, Spiegelaufnahme ohne Gesicht, von hinten beim Gehen",
            ),
            "character_base": first_sentence(
                character,
                "Die Figur wirkt wie eine reale Person im Alltag.",
            ),
            "orthosis_rules": _join_or_default(
                bullets(orthosis, "Pflicht"),
                "Orthese am linken Bein",
            ),
            "incontinence_rules": _join_or_default(
                bullets(incontinence, "Sichtbarkeit"),
                "alltagsbezogene Sichtbarkeit ohne sexualisierte Darstellung",
            ),
        }


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
