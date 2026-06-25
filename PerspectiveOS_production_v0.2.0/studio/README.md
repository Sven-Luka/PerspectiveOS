# Perspective Studio v0.2

Perspective Studio is a small Streamlit application for generating PerspectiveOS production briefs.

Version 0.2 is context-aware. It reads repository documentation from `creative/`, `visual/`, and `persona/` and uses deterministic template logic to create briefs. It does not call AI APIs.

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

## Generated Briefs

When `Generate Brief` is clicked, the app creates a Markdown file in:

```text
studio/generated/
```

Generated files use this naming format:

```text
YYYY-MM-DD_topic.md
```

Each generated file includes:

- Production Brief
- Topic
- Message
- Visual Idea
- Hook
- Caption
- Hashtags
- CTA
- Comment Strategy
- Image Prompt
- Video Prompt

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
- `production/`: workflow package for future production orchestration
- `analytics/`: local post-performance storage

Implemented service classes:

- `ProjectSettings`
- `RepositoryScanner`
- `KnowledgeIndex`
- `BriefGenerator`
- `AssetRegistry`
- `AnalyticsStore`
