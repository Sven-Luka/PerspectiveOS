import json
import os
import re
from dataclasses import replace
from pathlib import Path

import streamlit as st

try:
    from .analytics import ContentQuality, ContentQualityStore
    from .core.config import AID_VISIBILITY_OPTIONS, FORMAT_OPTIONS, IMAGE_TYPES, TARGET_EMOTIONS, TOPICS
    from .core.knowledge import bullets, load_repository_knowledge
    from .core.settings import ProjectSettings
    from .core.tights import BAND_RELATIONS, TIGHTS_DEN, band_relation_phrase, tights_phrase
    from .image import ImageGenerationError
    from .image.layout_composer import LayoutComposer, LayoutContent
    from .image.prompt_contract import ImagePromptContractBuilder
    from .image.reference_selector import ReferenceSelector
    from .image.visual_agent import VisualAgent
    from .production import ProductionFolderPipeline, ProductionRequest
    from .production.review import ProductionReviewer
except ImportError:
    from analytics import ContentQuality, ContentQualityStore
    from core.config import AID_VISIBILITY_OPTIONS, FORMAT_OPTIONS, IMAGE_TYPES, TARGET_EMOTIONS, TOPICS
    from core.knowledge import bullets, load_repository_knowledge
    from core.settings import ProjectSettings
    from core.tights import BAND_RELATIONS, TIGHTS_DEN, band_relation_phrase, tights_phrase
    from image import ImageGenerationError
    from image.layout_composer import LayoutComposer, LayoutContent
    from image.prompt_contract import ImagePromptContractBuilder
    from image.reference_selector import ReferenceSelector
    from image.visual_agent import VisualAgent
    from production import ProductionFolderPipeline, ProductionRequest
    from production.review import ProductionReviewer


st.set_page_config(page_title="Perspective Studio", page_icon="PS", layout="centered")

knowledge = load_repository_knowledge()
settings = ProjectSettings()


def outfit_suggestions() -> list[str]:
    """Return preferred outfit options from the repository OutfitGuide."""
    return bullets(knowledge.document("persona/OutfitGuide.md"), "Bevorzugt")


def metaphor_suggestions() -> list[str]:
    """Return metaphor names (the '## ' headings) from the MetaphorLibrary."""
    content = knowledge.document("creative/MetaphorLibrary.md")
    return re.findall(r"^##\s+(.+?)\s*$", content, flags=re.MULTILINE)


def _set_field(state_key: str, value: str) -> None:
    """Callback: write a bubble value into the bound form field."""
    st.session_state[state_key] = value


def render_bubbles(label: str, options: list[str], state_key: str, columns: int = 4) -> None:
    """Render clickable suggestion bubbles that fill a form field on click."""
    if not options:
        return
    st.caption(label)
    cols = st.columns(columns)
    for index, option in enumerate(options):
        cols[index % columns].button(
            option,
            key=f"{state_key}_bubble_{index}",
            on_click=_set_field,
            args=(state_key, option),
            use_container_width=True,
        )

with st.sidebar:
    st.header("Repository Knowledge")
    st.subheader("Loaded documents")
    if knowledge.loaded_documents:
        for document in knowledge.loaded_documents:
            st.write(f"- {document}")
    else:
        st.write("None")

    st.subheader("Missing documents")
    if knowledge.missing_documents:
        for document in knowledge.missing_documents:
            st.write(f"- {document}")
    else:
        st.write("None")

    st.subheader("Last refresh")
    st.write(knowledge.last_refresh)

    st.divider()
    st.subheader("Image Generation")
    env_key = os.environ.get("OPENAI_API_KEY", "")
    if env_key:
        st.caption("OpenAI API key loaded from environment.")
    api_key = st.text_input(
        "OpenAI API key",
        value="",
        type="password",
        help="Used for GPT prompts/review and gpt-image-1. Leave empty to use the OPENAI_API_KEY environment variable.",
    )

    backend_choice = st.selectbox(
        "Image backend",
        ["openai", "runpod_flux"],
        help="openai = gpt-image-1 (content-moderated). runpod_flux = RunPod ComfyUI/Flux (no prefilter).",
    )
    os.environ["IMAGE_BACKEND"] = backend_choice
    if backend_choice == "runpod_flux":
        if os.environ.get("RUNPOD_API_KEY") and os.environ.get("RUNPOD_FLUX_ENDPOINT"):
            st.caption("RunPod Flux endpoint loaded from environment.")
        else:
            st.warning("Set RUNPOD_API_KEY and RUNPOD_FLUX_ENDPOINT in the environment.")

st.title("Perspective Studio")
st.divider()

st.header("Create New Post")

st.subheader("Quick fill")
render_bubbles("Outfit suggestions (click to fill)", outfit_suggestions(), "outfit_input")
render_bubbles("Metaphor suggestions (click to fill)", metaphor_suggestions(), "metaphor_input")

with st.form("create_new_post"):
    topic = st.selectbox("Topic", TOPICS)
    target_emotion = st.selectbox("Target Emotion", TARGET_EMOTIONS)
    image_type = st.selectbox("Image Type", IMAGE_TYPES)
    location = st.text_input("Location")
    outfit = st.text_input("Outfit", key="outfit_input")
    tights_color = st.selectbox("Strumpfhose – Farbe", ["schwarz", "weiß", "hautfarben (Glanz)"])
    tights_den = st.selectbox(
        "Strumpfhose – DEN",
        TIGHTS_DEN,
        index=TIGHTS_DEN.index(20),
        help="Niedriger DEN = transparenter ⇒ Windelbund/blaue Schiene schimmern stärker durch. "
        "Höher = blickdicht. Weiß wirkt bei gleichem DEN deckender als Schwarz.",
    )
    band_relation = st.selectbox(
        "Bund-Verhältnis (Strumpfhose vs. Windel)",
        BAND_RELATIONS,
        help="Fall A: Strumpfhosenbund höher, Windelbund schimmert darunter durch. "
        "Fall B: Strumpfhosenbund tiefer, der weiße Windelbund schaut oben direkt heraus.",
    )
    aid_visibility = st.selectbox("Aid visibility", AID_VISIBILITY_OPTIONS, index=3)
    metaphor = st.text_input("Metaphor", key="metaphor_input")
    format_name = st.selectbox("Format", FORMAT_OPTIONS)
    free_story = st.text_area(
        "Creator Story Brief (optional)",
        help="Paste a complete carousel idea here. Perspective keeps it as the story contract and adds the CI, character, photo, and layout rules automatically.",
        height=220,
    )
    include_outfit_tip = st.checkbox("Include occasional outfit/source tip")
    outfit_source_url = st.text_input(
        "Verified outfit source URL (optional)",
        help="For example, a checked Amazon product page. The link is stored only in the production artifact and must be disclosed appropriately before publishing.",
        disabled=not include_outfit_tip,
    )

    submitted = st.form_submit_button("Generate Brief")


def _render_artifact(file_name: str, content: str) -> None:
    st.download_button(
        f"Download {file_name}",
        data=content,
        file_name=file_name,
        mime="text/markdown",
    )
    st.markdown(content)


def _ensure_review_artifacts(files: dict[str, str]) -> None:
    """Backfill automation review files for older folders kept in Streamlit state."""
    backfilled = False
    if "image_contract.md" not in files:
        files["image_contract.md"] = _image_contract_markdown()
        backfilled = True
    if "reference_manifest.md" not in files or "reference_manifest.json" not in files:
        manifest_md, manifest_json = _reference_manifest(files)
        files["reference_manifest.md"] = manifest_md
        files["reference_manifest.json"] = manifest_json
        backfilled = True
    if (
        not backfilled
        and "automation_review.md" in files
        and "automation_review.json" in files
    ):
        return
    review = ProductionReviewer(knowledge).review(files)
    files["automation_review.md"] = review.to_markdown()
    files["automation_review.json"] = review.to_json()


def _image_contract_markdown() -> str:
    contract = ImagePromptContractBuilder(knowledge).build()
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


def _markdown_bullets(values: list[str]) -> str:
    if not values:
        return "- No source values found."
    return "\n".join(f"- {value}" for value in values)


def _reference_manifest(files: dict[str, str]) -> tuple[str, str]:
    metadata = _metadata_payload(files)
    selector = ReferenceSelector(settings)
    references = selector.select(
        topic=str(metadata.get("topic", "")),
        location=str(metadata.get("location", "")),
        outfit=str(metadata.get("outfit", "")),
        aid_visibility=str(metadata.get("aid_visibility", "")),
    )
    return selector.manifest_markdown(references), selector.manifest_json(references)


def _artifact_content(files: dict[str, str], file_name: str) -> str:
    """Return artifact content without crashing when older session state is incomplete."""
    if file_name not in files:
        _ensure_review_artifacts(files)
    if file_name in files:
        return files[file_name]
    return (
        f"# Missing Artifact\n\n"
        f"`{file_name}` is not available in this production folder state. "
        "Generate the post again to rebuild the folder with the current automation contract.\n"
    )


def _metadata_payload(files: dict[str, str]) -> dict[str, object]:
    try:
        return json.loads(files.get("metadata.json", "{}"))
    except json.JSONDecodeError:
        return {}


if submitted:
    show_diaper = aid_visibility in ("diaper", "both")
    outfit_full = ", ".join(
        part for part in [outfit.strip(), tights_phrase(tights_den, tights_color, show_diaper)] if part
    )
    # The diaper-vs-tights waistband layering only matters when the diaper is shown on the body.
    band_phrase = band_relation_phrase(band_relation) if aid_visibility in ("diaper", "both") else ""
    aid_visibility_full = ". ".join(part for part in [aid_visibility, band_phrase] if part)
    request = ProductionRequest(
        topic=topic,
        target_emotion=target_emotion,
        image_type=image_type,
        location=location,
        outfit=outfit_full,
        aid_visibility=aid_visibility_full,
        metaphor=metaphor,
        format_name=format_name,
        free_story=free_story,
        include_outfit_tip=include_outfit_tip,
        outfit_source_url=outfit_source_url,
    )
    production_folder = ProductionFolderPipeline(knowledge, settings).create(request)
    st.session_state["production_folder"] = production_folder
    st.session_state["production_format"] = format_name
    st.session_state.pop("generated_image", None)

production_folder = st.session_state.get("production_folder")

if production_folder is not None:
    _ensure_review_artifacts(production_folder.files)
    st.success(f"Production folder generated: {production_folder.folder_name}")
    st.markdown(f"`{production_folder.relative_path}`")
    st.markdown("### Generated Files")
    for file_name in production_folder.files:
        st.write(f"- {file_name}")

    st.divider()
    st.header("Creator Rating")
    st.caption("Four- and five-star folders are copied into the validated reference library with their story and available images.")
    rating_key = f"rating_{production_folder.folder_name}"
    notes_key = f"rating_notes_{production_folder.folder_name}"
    rating = st.slider("Quality", min_value=1, max_value=5, value=5, key=rating_key)
    rating_notes = st.text_area("What worked or should change next time?", key=notes_key)
    if st.button("Save rating", key=f"save_{production_folder.folder_name}"):
        quality = ContentQualityStore(settings).rate(
            ContentQuality(
                post_id=production_folder.folder_name,
                stars=rating,
                notes=rating_notes,
            ),
            settings.generated_dir / production_folder.folder_name,
        )
        st.success(f"Saved {quality.stars}/5 stars. High-rated outputs are in {settings.validated_posts_dir}.")

    (
        brief_tab,
        hooks_tab,
        caption_tab,
        carousel_tab,
        image_contract_tab,
        references_tab,
        comments_tab,
        story_tab,
        review_tab,
        image_review_tab,
    ) = st.tabs(
        [
            "Brief",
            "Hooks",
            "Caption",
            "Carousel",
            "Image Contract",
            "References",
            "Comments",
            "Story",
            "Review",
            "Image Review",
        ]
    )

    with brief_tab:
        _render_artifact("brief.md", _artifact_content(production_folder.files, "brief.md"))

    with hooks_tab:
        _render_artifact("hooks.md", _artifact_content(production_folder.files, "hooks.md"))

    with caption_tab:
        _render_artifact("caption.md", _artifact_content(production_folder.files, "caption.md"))

    with carousel_tab:
        _render_artifact("carousel.md", _artifact_content(production_folder.files, "carousel.md"))

    with image_contract_tab:
        _render_artifact(
            "image_contract.md",
            _artifact_content(production_folder.files, "image_contract.md"),
        )

    with references_tab:
        _render_artifact(
            "reference_manifest.md",
            _artifact_content(production_folder.files, "reference_manifest.md"),
        )

    with comments_tab:
        _render_artifact("comments.md", _artifact_content(production_folder.files, "comments.md"))

    with story_tab:
        _render_artifact("story.md", _artifact_content(production_folder.files, "story.md"))
        if "story_source.md" in production_folder.files:
            st.markdown("### Creator Story Source")
            _render_artifact("story_source.md", production_folder.files["story_source.md"])

    with review_tab:
        _render_artifact(
            "automation_review.md",
            _artifact_content(production_folder.files, "automation_review.md"),
        )

    with image_review_tab:
        _render_artifact(
            "image_review.md",
            _artifact_content(production_folder.files, "image_review.md"),
        )

    st.divider()
    st.header("Generate Image")
    st.markdown(
        "Uses the `image_prompt.md` from this folder with the selected image backend "
        "(OpenAI gpt-image-1 or RunPod/Flux — see sidebar)."
    )

    with st.expander("Image prompt", expanded=False):
        st.markdown(_artifact_content(production_folder.files, "image_prompt.md"))

    if st.button("Generate Image With Visual Agent v1"):
        effective_key = api_key.strip() or env_key
        if not effective_key:
            st.error("No OpenAI API key. Enter one in the sidebar or set OPENAI_API_KEY.")
        else:
            folder_path = settings.generated_dir / production_folder.folder_name
            image_format = st.session_state.get("production_format", "Feed 4:5")
            metadata = _metadata_payload(production_folder.files)
            with st.spinner("Running Visual Agent v1 with selected references..."):
                try:
                    result = VisualAgent(effective_key, knowledge, settings).run(
                        prompt=_artifact_content(production_folder.files, "image_prompt.md"),
                        folder_path=folder_path,
                        format_name=image_format,
                        topic=str(metadata.get("topic", "")),
                        location=str(metadata.get("location", "")),
                        outfit=str(metadata.get("outfit", "")),
                        aid_visibility=str(metadata.get("aid_visibility", "")),
                        repository_root=settings.repository_root,
                        carousel_content=_artifact_content(production_folder.files, "carousel.md"),
                    )
                    production_folder.files["reference_manifest.md"] = (
                        folder_path / "reference_manifest.md"
                    ).read_text(encoding="utf-8")
                    production_folder.files["image_review.md"] = (
                        folder_path / "image_review.md"
                    ).read_text(encoding="utf-8")
                    st.session_state["generated_image"] = result.image
                    st.session_state["composed_layout"] = result.layout
                    st.session_state["carousel_layouts"] = list(result.carousel_layouts)
                    st.session_state["slide_contents"] = list(result.slide_contents)
                    st.session_state["base_image_paths"] = [str(p) for p in result.base_image_paths]
                    st.session_state["visual_agent_review"] = result.review
                except ImageGenerationError as error:
                    st.session_state.pop("generated_image", None)
                    st.session_state.pop("composed_layout", None)
                    st.session_state.pop("carousel_layouts", None)
                    st.session_state.pop("slide_contents", None)
                    st.session_state.pop("base_image_paths", None)
                    st.session_state.pop("visual_agent_review", None)
                    st.error(str(error))

    generated_image = st.session_state.get("generated_image")
    if generated_image is not None:
        st.success(f"Image saved: {generated_image.relative_path}")
        visual_review = st.session_state.get("visual_agent_review")
        if visual_review is not None:
            st.info(f"Visual Agent review status: {visual_review.status.upper()}")
        st.image(generated_image.image_bytes)
        composed_layout = st.session_state.get("composed_layout")
        if composed_layout is not None:
            st.success(f"First carousel slide saved: {composed_layout.relative_path}")
        carousel_layouts = st.session_state.get("carousel_layouts", [])
        slide_contents = st.session_state.get("slide_contents", [])
        base_paths = st.session_state.get("base_image_paths", [])
        editable = (
            len(slide_contents) == len(carousel_layouts)
            and len(base_paths) == len(carousel_layouts)
            and len(carousel_layouts) > 0
        )
        if editable:
            st.caption(
                "Text und Herz pro Slide anpassbar - 'Aktualisieren' baut nur das Overlay neu, "
                "ohne ein neues Bild zu generieren."
            )
        for index, layout in enumerate(carousel_layouts):
            st.image(layout.image_bytes)
            if editable:
                content = slide_contents[index]
                with st.expander(f"Text & Herz bearbeiten - Slide {index + 1}", expanded=False):
                    key = f"edit_{index}"
                    new_series = st.text_input("Label (oben)", value=content.series_label, key=f"{key}_series")
                    new_headline = st.text_input("Headline", value=content.headline, key=f"{key}_head")
                    new_highlight = st.text_input("Highlight", value=content.highlight, key=f"{key}_high")
                    new_body = st.text_input("Fliesstext (nur Detail-Slides)", value=content.body_text, key=f"{key}_body")
                    new_icons = st.text_input(
                        "Badge-Icons (Komma-getrennt)", value=", ".join(content.icon_labels), key=f"{key}_icons"
                    )
                    new_heart = st.checkbox("Gelbes Herz oben anzeigen", value=content.show_heart, key=f"{key}_heart")
                    if st.button("Aktualisieren", key=f"{key}_update"):
                        updated = replace(
                            content,
                            series_label=new_series,
                            headline=new_headline,
                            highlight=new_highlight,
                            body_text=new_body,
                            icon_labels=tuple(part.strip() for part in new_icons.split(",") if part.strip()),
                            show_heart=new_heart,
                        )
                        folder_path = settings.generated_dir / production_folder.folder_name
                        recomposed = LayoutComposer(settings).compose_feed_slide(
                            source_image=Path(base_paths[index]),
                            folder_path=folder_path,
                            content=updated,
                            file_name=layout.file_name,
                            repository_root=settings.repository_root,
                        )
                        st.session_state["carousel_layouts"][index] = recomposed
                        st.session_state["slide_contents"][index] = updated
                        st.rerun()
            st.download_button(
                f"Download carousel slide {index + 1}",
                data=layout.image_bytes,
                file_name=layout.file_name,
                mime="image/png",
                key=f"dl_slide_{index}",
            )
        st.download_button(
            f"Download {generated_image.file_name}",
            data=generated_image.image_bytes,
            file_name=generated_image.file_name,
            mime="image/png",
        )
