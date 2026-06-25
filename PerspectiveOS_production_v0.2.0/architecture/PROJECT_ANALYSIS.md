# Project Analysis

## 1. Summary of the Repository

Perspective OS is a structured brand, content, and production operating system for a German-language lifestyle and inclusion channel. The repository defines the creative strategy, brand rules, visual standards, persona constraints, prompt library, design governance, and first-season post briefings for a channel centered on Alltag, Mode, Humor, Perspektivwechsel, and selbstverstaendliche Sichtbarkeit.

This is not yet a conventional software application repository. It is primarily a Markdown-based knowledge base with one small Python utility for generating new post brief drafts. Its current architecture is optimized for human and AI-assisted creative production: the source material acts as a shared operating manual for content strategy, image generation, carousel production, caption writing, design review, and future automation.

The most important product principle is consistent across the repository:

> Lifestyle leads. Assistive devices accompany.

In practice, the repository aims to ensure that orthosis, incontinence products, clothing, humor, and visibility are handled with dignity, consistency, and clear creative boundaries.

## 2. Folder Structure

```text
PerspectiveOS_production_v0.2.0/
+-- assets/
|   +-- ASSET_CATALOG.md
+-- automation/
|   +-- CODEX_BRIEF.md
+-- brand/
|   +-- Manifest.md
|   +-- Positioning.md
|   +-- Values.md
+-- creative/
|   +-- CommentPlaybook.md
|   +-- CreatorBible.md
|   +-- LanguageBible.md
|   +-- MetaphorLibrary.md
+-- knowledge/
|   +-- checklists/
|   |   +-- design_review.md
|   +-- design-decisions/
|       +-- DDR-0001-human-before-aid.md
|       +-- DDR-0002-lifestyle-leads.md
|       +-- DDR-0003-visible-not-hidden.md
+-- persona/
|   +-- Character.md
|   +-- Incontinence.md
|   +-- Orthosis.md
|   +-- OutfitGuide.md
+-- posts/
|   +-- season01_anders_gedacht/
|       +-- 01_bauch_beine_po.md
|       +-- ...
|       +-- 15_wenn_du_nur_die_windel_siehst.md
+-- prompts/
|   +-- caption/
|   |   +-- caption_formula.md
|   +-- carousel/
|   |   +-- briefing_template.md
|   +-- image/
|       +-- master_image_prompt.md
+-- scripts/
|   +-- create_post_brief.py
+-- visual/
|   +-- CarouselSystem.md
|   +-- DesignSystem.md
|   +-- PhotoStyle.md
+-- CHANGELOG.md
+-- README.md
+-- ROADMAP.md
```

## 3. Purpose of Each Folder

### `assets/`

Holds the asset catalog and planned reference taxonomy. It currently defines categories for orthosis references, outfits, tights, shoes, and incontinence products. It is ready to become the index layer for future real image references, but does not yet contain actual image files or machine-readable metadata.

### `automation/`

Contains the Codex working brief. This file defines the technical role of Codex, the expected division between creative direction and technical direction, and the near-term automation tasks such as Markdown linting, post briefing generation, and asset indexing.

### `brand/`

Defines the strategic core of Perspective: manifest, positioning, values, target feeling, and negative positioning. This folder answers what the channel is, what it is not, and what emotional and ethical constraints should guide production.

### `creative/`

Defines the creative operating layer: the Creator Bible, Language Bible, metaphor library, and comment playbook. These files provide tone, narrative structure, humor boundaries, preferred and avoided wording, reply patterns, and reusable metaphor systems.

### `knowledge/`

Acts as the governance and quality layer. It contains design review checklists and design decision records. The DDR files preserve important strategic decisions such as "Der Mensch steht vor dem Hilfsmittel", "Lifestyle fuehrt", and "Selbstverstaendliche Sichtbarkeit".

### `persona/`

Defines the character and representation constraints. It includes physical appearance guidance, outfit rules, orthosis requirements, and incontinence visibility boundaries. This folder is critical for image consistency and for avoiding harmful or fetishizing representation.

### `posts/`

Contains production-ready content briefings. The existing `season01_anders_gedacht` folder has 15 planned posts, each following a consistent structure: title, series, hook, why sentence, metaphor, carousel structure, caption approach, and design notes.

### `prompts/`

Stores reusable prompt and content templates. It currently includes a master image prompt, a carousel briefing template, and a caption formula. This folder is the bridge between strategic rules and repeatable AI-assisted production.

### `scripts/`

Contains lightweight local automation. The current `create_post_brief.py` script creates a draft post briefing from a hardcoded Markdown template and writes it to `posts/drafts/`.

### `visual/`

Defines the visual production standard: Instagram 4:5 format, smartphone documentary style, carousel structure, safety margins, color accents, photo perspectives, and layout rules.

## 4. Strengths

- Strong strategic clarity: the repo repeatedly reinforces a clear north star, "Der Mensch fuehrt. Das Hilfsmittel begleitet."
- Clear creative boundaries: the repository explicitly rejects pity, shock, oversexualization, fetish content, hidden-assistive-device narratives, and heroic "despite disability" framing.
- Good separation of concerns: brand, creative language, persona, visual rules, prompts, posts, and governance are separated into understandable folders.
- Production-ready content pipeline foundation: Season 1 has a complete set of briefings and a consistent carousel structure.
- Useful governance artifacts: design decision records and the review checklist make creative judgment auditable instead of purely subjective.
- AI-friendly source format: Markdown files are easy for humans, Codex, RAG systems, and future Studio tooling to parse.
- Repeatable creative grammar: the Language Bible, metaphor library, and carousel system create a repeatable rhythm without making every post identical.

## 5. Weaknesses

- No machine-readable content schema yet: post briefings are structured by headings, but there is no YAML front matter, JSON schema, or validation layer.
- Limited automation: only one script exists, and it uses a hardcoded template rather than the canonical `prompts/carousel/briefing_template.md`.
- No tests or validation commands: there are no checks for Markdown formatting, required headings, broken links, naming conventions, or content safety rules.
- No application layer: Perspective Studio is mentioned in the roadmap but does not yet exist as a tool, API, UI, or local workflow.
- Asset catalog is conceptual: the repo defines asset categories, but there is no asset index, metadata model, thumbnail generation, or linkage from posts to assets.
- Encoding risk visible in shell output: German umlauts and special characters appear as mojibake in terminal output, which suggests tooling should standardize UTF-8 handling.
- No lifecycle states for posts: briefings do not currently expose statuses such as draft, reviewed, visual-produced, caption-final, scheduled, posted, or archived.
- No explicit safety review workflow beyond the checklist: the qualitative standards are strong, but they are not enforceable by automation yet.
- No dependency or environment definition: there is no `requirements.txt`, `pyproject.toml`, `package.json`, Makefile, or task runner.

## 6. Suggestions for Improvements

1. Add front matter to post briefings.

   Each post could include stable metadata such as `id`, `season`, `status`, `series`, `topic`, `metaphor`, `required_assets`, `review_state`, and `publish_date`.

2. Define a formal post schema.

   Add a schema file under a future `schemas/` folder and validate all posts against it. This would turn the existing creative format into reliable production data.

3. Replace hardcoded script templates with repository templates.

   Update `scripts/create_post_brief.py` so it reads from `prompts/carousel/briefing_template.md` or a dedicated `templates/post_brief.md`.

4. Add Markdown and content validation.

   Useful checks:
   - required headings exist in every post
   - file names match numeric sequence conventions
   - internal links resolve
   - no banned language from the Language Bible appears accidentally
   - every image prompt includes orthosis-side consistency where relevant

5. Create an asset metadata model.

   Move from a descriptive asset catalog to records such as:
   - asset id
   - category
   - source path
   - rights/usage notes
   - visible elements
   - linked posts
   - review status

6. Add a production workflow.

   Introduce explicit states from idea to published post:

   ```text
   idea -> briefing -> visual draft -> design review -> caption final -> scheduled -> posted -> analyzed
   ```

7. Add a `docs/` or `architecture/` area for technical decisions.

   Keep brand decisions in `knowledge/design-decisions/`, but use `architecture/` for software architecture, Studio plans, schemas, data flow, and automation decisions.

8. Standardize UTF-8 handling.

   Add editor/tooling guidance so German copy, typographic quotes, arrows, and emoji render consistently across scripts, terminals, and future Studio views.

## 7. Proposal for Perspective Studio Architecture

Perspective Studio should become the production interface on top of the existing Perspective OS knowledge base. The goal should not be to replace the Markdown repository, but to make it easier to generate, review, assemble, and publish content while preserving the creative rules already defined here.

### Architectural Principle

Use the repository as the source of truth.

Markdown remains the canonical creative source. Perspective Studio should read, validate, enrich, and write structured files back into the repo rather than trapping content inside an opaque app database.

### Proposed Layers

```text
Perspective Studio
+-- Source Layer
|   +-- Markdown documents
|   +-- Post briefings
|   +-- Prompt templates
|   +-- Design decisions
|   +-- Asset catalog
+-- Data Layer
|   +-- Markdown parser
|   +-- Front matter schema
|   +-- Asset metadata index
|   +-- Validation reports
+-- Intelligence Layer
|   +-- RAG over brand, creative, persona, visual, and knowledge files
|   +-- Prompt assembly
|   +-- Caption drafting
|   +-- Design review assistant
|   +-- Safety and tone checks
+-- Workflow Layer
|   +-- Post status tracking
|   +-- Review gates
|   +-- Task queues
|   +-- Export packages
+-- Interface Layer
    +-- Studio dashboard
    +-- Post editor
    +-- Asset browser
    +-- Prompt builder
    +-- Review checklist
    +-- Publishing calendar
```

### Suggested Technical Shape

For a first version, Perspective Studio can be a local-first web app:

- Frontend: React or Next.js for a structured editor, asset browser, and review dashboard.
- Backend: lightweight Node.js or Python service for filesystem access, Markdown parsing, schema validation, and AI orchestration.
- Storage: Markdown files plus sidecar metadata in YAML or JSON.
- Search/RAG: local embeddings over selected folders: `brand/`, `creative/`, `persona/`, `visual/`, `knowledge/`, and `prompts/`.
- Validation: command-line checks that can also run inside the Studio UI.
- Exports: generated post packages containing briefing, caption, image prompt, design checklist, and linked assets.

### Core Studio Modules

#### 1. Post Briefing Editor

Provides a form-based editor for the existing Season 1 structure. It should preserve Markdown output while reducing formatting mistakes.

Key features:
- create post from template
- edit hook, why sentence, metaphor, slides, caption approach, design notes
- assign lifecycle status
- run schema validation
- generate assembled image/caption prompts

#### 2. Brand and Safety Assistant

Uses the repository rules to check whether a post follows the Perspective OS constraints.

Checks should include:
- Lifestyle leads before assistive-device focus
- no pity framing
- no fetish-serving language
- no oversexualized image direction
- orthosis side consistency
- warm, respectful humor
- enough everyday context

#### 3. Asset Library

Turns `assets/ASSET_CATALOG.md` into a real production system.

Key features:
- scan `assets/` for files
- create metadata records
- show thumbnails
- tag by category
- link assets to posts
- mark usage rights and review status

#### 4. Prompt Builder

Combines the master image prompt, persona rules, visual rules, and specific post briefing into one production prompt.

The builder should make prompt assembly deterministic:

```text
master image prompt
+ relevant persona constraints
+ post-specific scene
+ visual format rules
+ safety exclusions
+ linked asset references
```

#### 5. Review Dashboard

Operationalizes `knowledge/checklists/design_review.md`.

Key features:
- checklist per post
- reviewer notes
- pass/fail state
- unresolved issues
- exportable review summary

#### 6. Publishing Calendar

Adds production planning without changing the creative source model.

Key features:
- season view
- scheduled date
- current status
- missing assets
- caption readiness
- visual readiness
- post-publish notes

### Recommended Initial Milestone

The best first milestone is not a full Studio UI. The strongest foundation would be a schema and validation CLI:

```text
scripts/
+-- create_post_brief.py
+-- validate_posts.py
+-- index_assets.py
schemas/
+-- post_brief.schema.json
```

This would make the current Markdown system reliable before adding interface complexity. Once validation, metadata, and indexing are stable, a Studio UI can sit on top of the same rules instead of inventing new ones.

### Target End State

Perspective Studio should feel like a production cockpit for a values-driven content system:

- brand rules remain visible
- creative work stays fast
- representation boundaries are protected
- assets are reusable and traceable
- every post moves through a clear lifecycle
- AI assistance is guided by the repository instead of improvising from scratch

The current repository is a strong foundation for that direction. Its next architectural step is to turn the existing human-readable operating system into a structured, validated, automation-ready production system.
