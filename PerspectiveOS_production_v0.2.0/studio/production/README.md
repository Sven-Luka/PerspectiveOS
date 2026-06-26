# Production

The `production` package contains workflow-oriented services for generated briefs, production folders, and publishing operations.

Responsibilities:

- coordinate production-ready artifacts
- create `studio/generated/YYYY-MM-DD_slug/` folders
- write `brief.md`, `hooks.md`, `caption.md`, `carousel.md`, `image_prompt.md`, `video_prompt.md`, `comments.md`, `story.md`, `checklist.md`, and `metadata.json`
- preserve a pasted creator story as `story_source.md`, then use its slide contract for `carousel.md` and `image_prompt.md`
- create `outfit_tip.md` only for intentionally selected, occasional outfit/source posts
- preserve repository-first workflows
- provide future review, scheduling, and export modules

Core classes:

- `ProductionRequest`
- `ProductionArtifactGenerator`
- `ProductionFolderPipeline`
