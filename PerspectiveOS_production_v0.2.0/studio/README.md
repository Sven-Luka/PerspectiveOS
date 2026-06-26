# Perspective Studio v0.5

Perspective Studio is a small Streamlit application for generating PerspectiveOS production briefs.

Version 0.4 turned the app into a modular Creative Director. It reads repository documentation from `creative/`, `visual/`, and `persona/` and uses deterministic template logic to create complete production folders, hooks, captions, carousels, comment strategy, and story sequences. The deterministic text generation does not call AI APIs.

Version 0.5 adds:

- **Image generation** via OpenAI `gpt-image-1`. A "Generate Image" button sends the folder's `image_prompt.md` to the API and writes the result as `image.png` into the production folder.
- **Quick-fill suggestion bubbles** for the `Outfit` and `Metaphor` fields. The bubbles are read at runtime from `persona/OutfitGuide.md` (the "Bevorzugt" list) and `creative/MetaphorLibrary.md` (the metaphor headings). One click fills the field; the value can still be edited.
- **Automation review** for every generated folder. The production pipeline writes `automation_review.md` and `automation_review.json` with required-file checks, metadata validation, and first-pass Creator/Language Bible gates.
- **Image contract generation** before image prompts. The pipeline writes `image_contract.md` from the master image prompt, Character Guide, Orthosis Guide, Design System, Carousel System, and Photo Style, then fails review if required prompt terms are missing.
- **Visual Agent v1** for reference-guided generation. The pipeline selects approved references from `assets/references/ASSET_INDEX.json`, writes `reference_manifest.md/json`, sends selected reference images with the image request, and writes `image_review.md/json` after generation.

## Setup

```bash
cd studio
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Run

```bash
cd studio
streamlit run app.py
```

Do not run Streamlit as an automated verification step because it starts a persistent server.

## Image Generation

Image generation uses OpenAI `gpt-image-1` and is billed per image (pay-per-use), independent of any ChatGPT subscription. A ChatGPT Plus/Pro plan does **not** cover API usage and cannot be used by the app.

Setup:

1. Add billing/credit at https://platform.openai.com/settings/organization/billing
2. Create an API key at https://platform.openai.com/api-keys
3. Provide the key either via the `OPENAI_API_KEY` environment variable or the sidebar field in the app.

Usage in the app:

1. Click `Generate Brief` to create a production folder.
2. In the `Generate Image` section, click `Generate Image`.
3. The image is saved as `image.png` in the production folder and shown with a download button.

Format-to-size mapping (gpt-image-1 supports fixed sizes):

- `Feed 4:5` and `Story 9:16` -> `1024x1536` (portrait)
- `Reel Cover` -> `1024x1024` (square)

Manual alternative (no API key): copy the generated `image_prompt.md` into ChatGPT, generate the image there, and place it in the production folder yourself.

## Verification

Use only non-persistent checks:

```bash
python -m compileall studio
python -c "import studio.app"
```

## Generated Production Folders

When `Generate Brief` is clicked, the app creates a production folder in:

```text
studio/generated/
```

Generated folders use this naming format:

```text
YYYY-MM-DD_slug/
```

Each generated folder includes:

- `brief.md`
- `hooks.md`
- `caption.md`
- `carousel.md`
- `image_contract.md`
- `reference_manifest.md`
- `reference_manifest.json`
- `image_prompt.md`
- `video_prompt.md`
- `comments.md`
- `story.md`
- `checklist.md`
- `metadata.json`
- `automation_review.md`
- `automation_review.json`
- `image.png` (only after `Generate Image` is used)

The UI shows generated content in tabs:

- Brief
- Hooks
- Caption
- Carousel
- Image Contract
- References
- Comments
- Story
- Review
- Image Review

Each tab has an individual download button for its artifact.

## Create New Post Fields

The main form supports:

- Topic
- Target Emotion
- Image Type
- Location
- Outfit
- Aid visibility
- Metaphor
- Format

### Quick-fill bubbles

Above the form, a `Quick fill` section shows clickable suggestion bubbles for `Outfit` and `Metaphor`. They are data-driven:

- Outfit bubbles come from the `Bevorzugt` list in `persona/OutfitGuide.md`.
- Metaphor bubbles come from the metaphor headings in `creative/MetaphorLibrary.md`.

Clicking a bubble fills the bound field via Streamlit session state. Bubbles live above the form because Streamlit only allows submit buttons inside a `st.form`. Editing the repository documents automatically updates the available bubbles, with no code change.

## Repository Knowledge

The sidebar shows:

- loaded documents
- missing documents
- last refresh time

The current knowledge set is:

- `creative/CreatorBible.md`
- `creative/LanguageBible.md`
- `creative/MetaphorLibrary.md`
- `visual/DesignSystem.md`
- `visual/PhotoStyle.md`
- `persona/Character.md`
- `persona/Incontinence.md`
- `persona/Orthosis.md`
- `persona/OutfitGuide.md`

## Modular Architecture

Perspective Studio is organized as a modular creator operating system:

- `core/`: settings, repository scanning, storage, and compatibility helpers
- `brain/`: knowledge indexing over repository documentation
- `creative/`: deterministic creative direction engines
- `image/`: asset registry plus image generation (OpenAI gpt-image-1)
- `production/`: production request models, artifact generators, and folder pipeline
- `analytics/`: local post-performance storage

Implemented service classes:

- `ProjectSettings`
- `RepositoryScanner`
- `KnowledgeIndex`
- `BriefGenerator`
- `HookEngine`
- `CaptionEngine`
- `CarouselEngine`
- `CommentEngine`
- `StoryEngine`
- `AssetRegistry`
- `ImageGenerator`
- `ReferenceSelector`
- `VisionReviewer`
- `VisualAgent`
- `AnalyticsStore`
- `ProductionReviewer`
- `ProductionArtifactGenerator`
- `ProductionFolderPipeline`
- `ProductionRequest`
