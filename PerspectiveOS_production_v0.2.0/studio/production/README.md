# Production

The `production` package contains workflow-oriented services for generated briefs, production folders, and publishing operations.

Responsibilities:

- coordinate production-ready artifacts
- create `studio/generated/YYYY-MM-DD_slug/` folders
- write `brief.md`, `caption.md`, `carousel.md`, `image_prompt.md`, `video_prompt.md`, `comments.md`, `checklist.md`, and `metadata.json`
- preserve repository-first workflows
- provide future review, scheduling, and export modules

Core classes:

- `ProductionRequest`
- `ProductionArtifactGenerator`
- `ProductionFolderPipeline`
