# Perspective Studio v0.3

Perspective Studio is a small Streamlit application for generating PerspectiveOS production briefs.

Version 0.3 is a production folder pipeline. It reads repository documentation from `creative/`, `visual/`, and `persona/` and uses deterministic template logic to create complete production folders. It does not call AI APIs.

## Setup

```bash
cd studio
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Run

```bash
streamlit run app.py
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
- `caption.md`
- `carousel.md`
- `image_prompt.md`
- `video_prompt.md`
- `comments.md`
- `checklist.md`
- `metadata.json`

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
- `creative/`: deterministic production brief generation
- `image/`: asset registry for future image assets and metadata
- `production/`: production request models, artifact generators, and folder pipeline
- `analytics/`: local post-performance storage

Implemented service classes:

- `ProjectSettings`
- `RepositoryScanner`
- `KnowledgeIndex`
- `BriefGenerator`
- `AssetRegistry`
- `AnalyticsStore`
- `ProductionArtifactGenerator`
- `ProductionFolderPipeline`
- `ProductionRequest`
