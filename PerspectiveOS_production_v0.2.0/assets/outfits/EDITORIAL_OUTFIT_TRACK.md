# Editorial Outfit Track

## Purpose

Outfit posts are an occasional practical service, not permanent advertising. They show how clothing can work with an orthosis, tights, products, or everyday movement while still supporting the actual story.

## Cadence

- Plan at most one outfit/source post for every five regular posts.
- Mix outfit detail, practical fit, and a normal everyday scene; never make every slide a product mention.
- A source is optional. Do not add a link just to fill the slot.

## Production Workflow

1. Choose an outfit from `persona/OutfitGuide.md` and the `assets/outfits/` cards.
2. Add or confirm a visual reference in `assets/references/outfits/` so the outfit is shown credibly.
3. In Studio, enable **Include occasional outfit/source tip** only for an eligible outfit post.
4. Add a personally checked source URL, for example a current Amazon product page, only after checking availability, material, fit, and price.
5. Studio creates `outfit_tip.md`; use its story integration paragraph in the carousel/caption rather than placing the link inside the image.
6. Before publishing, label affiliate or advertising links according to the platform and applicable rules. Do not present clothing as medical advice.

## Source Record

For every source that is actually used, create a small Markdown record in `assets/outfits/sources/`:

```md
# Product Name

- Status: checked YYYY-MM-DD
- Source: https://...
- Outfit fit: why it works with the selected outfit
- Story use: which practical moment it supports
- Disclosure: affiliate / non-affiliate / pending
```

Only `checked` records may be linked in a published caption.
