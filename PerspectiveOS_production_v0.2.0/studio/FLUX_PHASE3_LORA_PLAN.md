# Flux Phase 3 — Persona-LoRA über Network Volume

**Stand:** 2026-06-30 · **Ziel:** Referenz-Treue (konsistente Figur, Outfit, blaue
Bauerfeind-Orthese) für den RunPod/Flux-Backend, die text-only nicht liefert.
Mechanismus: eine **Persona-LoRA** auf den vorhandenen Referenzfotos, ausgeliefert per
**RunPod Network Volume**. Voraussetzung erledigt: Backend-Seam (`studio/image/backends/`),
Endpoint `husky_crimson_hyena` / Image `runpod/worker-comfyui:5.4.1-flux1-dev`.

---

## 1. Entscheidung & Rahmen

- **Delivery: Network Volume** (einmal einrichten, beliebig viele LoRAs, kein Image-Rebuild).
- Plain-LoRA = **Core-Node `LoraLoaderModelOnly`** → Network Volume reicht (Volume kann *keine*
  Custom-Nodes installieren, brauchen wir hier nicht).
- **Scope v1 = Persona-LoRA** (Körper + Outfit + Orthese). Das TENA-Produkt ist ein *Objekt* mit
  eigener Logik → optionale **zweite Produkt-LoRA** später, nicht in v1.
- **Vorteil Identität:** Die Persona ist bewusst **gesichtslos** — die LoRA lernt Körperbau,
  Outfit-Familie und Orthese, **kein reales Gesicht**. Sauber und ohne Personen-Likeness-Problem.

## 2. Network Volume (bestätigte Mechanik)

- Mount-Pfad im Container: **`/workspace`**.
- Modelle: `/workspace/models/loras/…`, `/workspace/models/checkpoints/…`, `…/vae/…`.
  ComfyUI erkennt sie **automatisch** (kein `extra_model_paths.yaml`, keine Symlinks).
- Attach: **Endpoint → Advanced → Select Network Volume** (Volume muss in der **gleichen Region**
  wie die Endpoint-GPU liegen).
- Workflow referenziert die LoRA per **bloßem Dateinamen** in `LoraLoaderModelOnly.lora_name`.

> Ziel-Datei: `/workspace/models/loras/perspective_jona_v1.safetensors`

## 3. Dataset (aus `assets/references/`)

Persona-Kern (eindeutige Quellbilder, teils mehrfach kategorisiert):
| Gruppe | Bilder | Zweck |
|---|---|---|
| `character/body_silhouette` | 10 | Körperbau, Proportionen, Haltung |
| `orthosis/front` + `side` + `details` | 10 + 3 + 2 | blaue Knieorthese, Seiten/Detail |
| `outfits/black_polo_black_shorts` | 10 | Outfit-Familie oben/unten |
| `outfits/tights_black` | 9 | schwarze Strumpfhose |

→ ~15–20 eindeutige Trainingsbilder (Überlappung herausgerechnet). Für eine Flux-LoRA
**ausreichend** (10–20 gute Bilder genügen).

**Vorbereitung (Skript `studio/training/build_lora_dataset.py`, neu):**
1. Eindeutige Persona-Bilder aus `ASSET_INDEX.json` ziehen (character/orthosis/outfits;
   `rejected` raus, Layout/Location/Schuhe raus).
2. Auf 1024 lange Kante normalisieren, in `dataset/jona/` ablegen.
3. Pro Bild eine `.txt`-Caption: **Trigger-Word `j0na`** + knappe Beschreibung
   (z. B. „j0na, androgynous person, black polo and black tights, blue knee orthosis on left leg,
   rear view"). Keine Gesichts-/Identitätsbegriffe.

## 4. Training (RunPod-GPU, ai-toolkit)

- **Tool:** `ai-toolkit` (ostris) — De-facto-Standard für Flux-LoRA.
- **Base:** `black-forest-labs/FLUX.1-dev` (gated → **HF-Token vorhanden**).
- **GPU-Pod:** 24 GB+ (4090 / L40 / A40), ~30–60 Min.
- **Config:** ~2000–3000 Steps, LR 1e-4, Rank 16–32, Auflösung 1024, Trigger `j0na`.
- **Output:** `perspective_jona_v1.safetensors` → auf das Network Volume nach
  `/workspace/models/loras/`.
- Dataset + Config liegen ebenfalls auf dem Volume (überlebt Pod-Stopp).

## 5. Backend-Anpassung (klein, vorbereitbar)

In `studio/image/backends/runpod_flux.py`:
- Optional `lora_name` + `lora_strength` (aus Env `FLUX_LORA_NAME` / Setting).
- Node **`LoraLoaderModelOnly`** zwischen `UNETLoader (12)` und den Modell-Verbrauchern
  (`BasicGuider 22`, `BasicScheduler 17`) einhängen:
  `model: [12,0] → LoraLoader → [22,17]`.
- Trigger-Word `j0na` automatisch dem Prompt voranstellen, wenn LoRA aktiv.
- **Abwärtskompatibel:** ohne `FLUX_LORA_NAME` exakt das heutige text→image-Verhalten.

## 6. Schritte & Verifikation

1. **Backend-LoRA-Hook** bauen (Code, inaktiv ohne LoRA) — *kann sofort passieren*.
2. **Dataset-Skript** + Captions erzeugen (lokal, keine Kosten).
3. **Network Volume** anlegen + an Endpoint hängen (RunPod-Konsole, dein Handgriff).
4. **Training-Pod** starten, LoRA trainieren, auf Volume ablegen.
5. **`FLUX_LORA_NAME=perspective_jona_v1.safetensors`** setzen, `poc_blocked`-Motiv neu rendern.
   *Verif.:* Orthese (blaues Knie) + Outfit + Körperbau deutlich treuer als text-only.
6. Iterieren (Steps/Rank/Strength), bei Bedarf v2.

## 7. Offene Punkte / Risiken

- **Kosten:** GPU-Pod-Zeit fürs Training (gering, einmalig) + minimale Volume-Monatskosten.
- **Region:** Volume muss zur Endpoint-GPU-Region passen — vor dem Anlegen prüfen.
- **TENA-Treue** bleibt v1 offen (separate Produkt-LoRA oder weiter via Text/Referenz).
- **Captions/Trigger** bestimmen die Qualität — ggf. 1–2 Trainingsläufe nötig.

---

### Sofort machbar ohne Kosten
Schritt 1 (Backend-LoRA-Hook) + Schritt 2 (Dataset-Skript) — danach brauchst du nur noch
Volume anlegen + Training starten.
