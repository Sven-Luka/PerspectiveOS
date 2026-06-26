# Perspective Carousel Master v2

These four images are the approved visual reference family for Perspective Studio's deterministic overlay composer.
They document the intended energy, not copyable slide wording.

## Master Slides

- `hook_selfie_v2.png`: strong first slide. Mirror selfie, face hidden, motif on the right, bold but playful paper-strip hook on the left.
- `icon_tip_v2.png`: airy tip slide. One clear thought, three warm icon badges with labels centered below, seated self-shot perspective.
- `explanation_text_v2.png`: text-first explanatory slide. A readable column leads; the face-hidden selfie remains a quiet supporting element.
- `cta_photo_v2.png`: photo-led closing slide. A different movement and location, a single follow action, no empty memorial-card ending.

## CI Rules Derived From The Masters

- Use purple, lavender, chartreuse, turquoise, warm off-white, and black only as an accent palette; never use black panels behind text.
- Use irregular paper strips and hand-drawn accents sparingly. Text is centered inside each strip with generous breathing room.
- Use a face-hidden, non-model, natural phone/selfie or documentary perspective. Keep the character's known silhouette, high ponytail, outfit family, and viewer-left orthosis consistent.
- Slide 1 is dense enough to stop the scroll. Slides 2 and 3 have more air. A text-first slide is allowed when the explanation needs it.
- The final slide remains a real image, uses a distinct scene, and carries the `made by Jona` signature plus one clear follow action.
- Use the supplied UI Kit icons or the deterministic icon renderer. Icon labels are always centered directly below their icon.

## Use In Studio

The image model creates clean photo bases. `studio/image/layout_composer.py` owns text, labels, icons, counters, bottom band, and signature deterministically. These master images are visual QA references for that composer and must not be supplied to the image model as literal text/layout inputs.
