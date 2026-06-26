# Image

The `image` package contains the asset registry and image generation.

Responsibilities:

- discover image files in `assets/` (`AssetRegistry`)
- read adjacent or catalogued Markdown metadata
- provide reusable asset records to creative and production workflows
- generate production images from an image prompt via OpenAI gpt-image-1 (`ImageGenerator`)
- select approved reference images from `assets/references/ASSET_INDEX.json` (`ReferenceSelector`)
- run reference-guided visual production with manifest and review outputs (`VisualAgent`)
- compose deterministic Perspective UI overlays after image generation (`LayoutComposer`)

## ImageGenerator

`ImageGenerator(api_key).generate(prompt, folder_path, format_name)` sends the prompt to OpenAI `gpt-image-1`, decodes the returned base64 image, and writes `image.png` into the given production folder. It raises `ImageGenerationError` for missing key, missing `openai` package, or API errors.

Format-to-size mapping:

- `Feed 4:5`, `Story 9:16` -> `1024x1536`
- `Reel Cover` -> `1024x1024`

The API key is read from the sidebar field or the `OPENAI_API_KEY` environment variable. Generation is billed per image and is independent of any ChatGPT subscription.

## Visual Agent v1

`VisualAgent` is the first closed-loop image workflow:

1. Select approved references for layout, character, orthosis, outfit, and location.
2. Write `reference_manifest.md` and `reference_manifest.json` into the production folder.
3. Generate the image with selected reference images attached.
4. Compose `layout_preview.png` from the clean image and deterministic UI-kit rules.
5. Write `image_review.md` and `image_review.json` with deterministic and semantic checks plus a correction prompt.

The review checks files, dimensions, prompt-contract coverage, required reference groups, and semantic visual issues such as visible face, copied layout text, wrong orthosis, collage/infographic output, or over-staged imagery. Layout reference screenshots must not be passed as generation images; they are used only by the deterministic composer.

## LayoutComposer

`LayoutComposer` takes a clean generated photo and creates `layout_preview.png` with Perspective colors, badges, highlight text, icon row, slide counter, and branding. This avoids asking the image model to invent or copy layout text.
