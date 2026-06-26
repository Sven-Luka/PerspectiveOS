import json
from datetime import datetime

try:
    from ..brain.index import IndexedKnowledge
    from ..core.knowledge import blockquotes, bullets, first_sentence
    from ..creative.brief_generator import BriefGenerator, TOPIC_PROFILES
    from ..creative.caption_engine import CaptionEngine
    from ..creative.carousel_engine import CarouselEngine
    from ..creative.comment_engine import CommentEngine
    from ..creative.context import CreativeInputs
    from ..creative.hook_engine import HookEngine
    from ..creative.story_engine import StoryEngine
    from ..image.prompt_contract import ImagePromptContractBuilder, render_image_prompt_contract
    from ..image.reference_selector import ReferenceSelector
    from .free_story import FreeStoryBrief
except ImportError:
    from brain.index import IndexedKnowledge
    from core.knowledge import blockquotes, bullets, first_sentence
    from creative.brief_generator import BriefGenerator, TOPIC_PROFILES
    from creative.caption_engine import CaptionEngine
    from creative.carousel_engine import CarouselEngine
    from creative.comment_engine import CommentEngine
    from creative.context import CreativeInputs
    from creative.hook_engine import HookEngine
    from creative.story_engine import StoryEngine
    from image.prompt_contract import ImagePromptContractBuilder, render_image_prompt_contract
    from image.reference_selector import ReferenceSelector
    from production.free_story import FreeStoryBrief
from .models import ProductionRequest


class ProductionArtifactGenerator:
    """Generates deterministic production artifacts from a request and repository knowledge."""

    def __init__(self, knowledge: IndexedKnowledge) -> None:
        """Create an artifact generator bound to the current KnowledgeIndex output."""
        self.knowledge = knowledge

    def generate_all(self, request: ProductionRequest) -> dict[str, str]:
        """Generate every file required for a production folder."""
        context = self._context(request)
        inputs = self._inputs(request)
        story_brief = FreeStoryBrief(request.free_story)
        carousel = story_brief.carousel_markdown(request.format_name) or CarouselEngine(self.knowledge).generate(inputs)
        image_prompt = self.image_prompt(context)
        if story_brief.is_present:
            image_prompt = f"{image_prompt}\n\n{story_brief.prompt_addendum()}"
        files = {
            "brief.md": self.brief(context, request),
            "hooks.md": HookEngine(self.knowledge).generate(inputs),
            "caption.md": CaptionEngine(self.knowledge).generate(inputs),
            "carousel.md": carousel,
            "image_contract.md": self.image_contract(),
            "reference_manifest.md": self.reference_manifest(context),
            "reference_manifest.json": self.reference_manifest_json(context),
            "image_prompt.md": image_prompt,
            "video_prompt.md": self.video_prompt(context),
            "comments.md": CommentEngine(self.knowledge).generate(inputs),
            "story.md": StoryEngine(self.knowledge).generate(inputs),
            "checklist.md": self.checklist(context),
            "metadata.json": self.metadata(context),
        }
        if story_brief.is_present:
            files["story_source.md"] = f"# Creator Story Source\n\n{story_brief.source}\n"
        if request.include_outfit_tip:
            files["outfit_tip.md"] = self.outfit_tip(context, request.outfit_source_url)
        return files

    def outfit_tip(self, context: dict[str, str], source_url: str) -> str:
        """Create an occasional, clearly disclosed outfit recommendation artifact."""
        source = source_url.strip() or "No source URL supplied. Add only a verified product link before publishing."
        return f"""# Outfit Tip

## Editorial Role
Use this as an occasional practical add-on, not as the main point of the post. The outfit supports the story: {context["outfit"]}.

## Story Integration
Show the item in a natural outfit or preparation moment. Explain why it is comfortable, workable with the orthosis, or useful in everyday movement. Do not turn the post into a product catalogue.

## Source
{source}

## Publishing Guardrails
- Use only a personally checked and current source.
- Mark affiliate or advertising links transparently where required.
- Keep a clear distinction between personal recommendation and medical advice.
- Schedule this format sparingly: normally no more than one outfit/source post in five regular posts.
"""

    def _inputs(self, request: ProductionRequest) -> CreativeInputs:
        """Convert a production request into creative engine inputs."""
        return CreativeInputs(
            topic=request.topic,
            target_emotion=request.target_emotion,
            image_type=request.image_type,
            location=request.location,
            outfit=request.outfit,
            aid_visibility=request.aid_visibility,
            metaphor=request.metaphor,
            format_name=request.format_name,
        )

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
        contract = ImagePromptContractBuilder(self.knowledge).build()
        return render_image_prompt_contract(
            contract,
            format_name=context["format_name"],
            scene=context["scene"],
            location=context["location"],
            outfit=context["outfit"],
            aid_visibility=context["aid_visibility"],
            metaphor=context["metaphor"],
            metaphor_line=context["metaphor_line"],
        )

    def image_contract(self) -> str:
        """Generate the explicit image contract used by the prompt and review gate."""
        contract = ImagePromptContractBuilder(self.knowledge).build()
        return f"""# Image Contract

This file is the deterministic source contract for image generation. The image prompt must preserve these values.

## Character Body
{_markdown_bullets(contract.character_body)}

## Character Hair
{_markdown_bullets(contract.character_hair)}

## Character Face
{_markdown_bullets(contract.character_face)}

## Character Pose
{_markdown_bullets(contract.character_pose)}

## Orthosis Required
{_markdown_bullets(contract.orthosis_required)}

## Orthosis Not Allowed
{_markdown_bullets(contract.orthosis_forbidden)}

## Format
{_markdown_bullets(contract.design_format)}

## Style
{_markdown_bullets(contract.design_style)}

## Layout
{_markdown_bullets(contract.design_layout)}

## Text Rules
{_markdown_bullets(contract.design_text_rules)}

## Carousel Guard
- {contract.carousel_standard}
- {contract.carousel_rule}

## Photo Perspectives
{_markdown_bullets(contract.photo_perspectives)}

## Required Prompt Terms
{_markdown_bullets(list(contract.required_terms))}
"""

    def reference_manifest(self, context: dict[str, str]) -> str:
        """Generate the selected visual reference manifest for this production run."""
        selector = ReferenceSelector()
        references = selector.select(
            topic=context["topic"],
            location=context["location"],
            outfit=context["outfit"],
            aid_visibility=context["aid_visibility"],
        )
        return selector.manifest_markdown(references)

    def reference_manifest_json(self, context: dict[str, str]) -> str:
        """Generate machine-readable selected reference metadata."""
        selector = ReferenceSelector()
        references = selector.select(
            topic=context["topic"],
            location=context["location"],
            outfit=context["outfit"],
            aid_visibility=context["aid_visibility"],
        )
        return selector.manifest_json(references)

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


def _markdown_bullets(values: list[str]) -> str:
    if not values:
        return "- No source values found."
    return "\n".join(f"- {value}" for value in values)


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
