# Flux/Redux Bild-Backend — Integrationsplan

**Stand:** 2026-06-30 · **Ziel:** OpenAI gpt-image-1 als alleiniges Bild-Backend ablösen/ergänzen
durch **Flux (Redux/Kontext)**, weil (a) gpt-image-1 das Windel-/Unterwäsche-/Strumpfhosen-Thema
zu aggressiv als „sexual" blockt (dokumentiert in `SESSION_2026-06-27.md` §6) und (b) wir
Referenz-konditionierte Generierung brauchen.

> Status v0.2.0: 100 % gpt-image-1. Flux war beschlossener nächster Schritt, aber **nie gebaut**.

---

## 1. Was heute existiert (Ist-Zustand)

- `image/generator.py` → `ImageGenerator` (MODEL `gpt-image-1`): `generate()` (text→img) und
  `generate_with_references()` (`client.images.edit` mit mehreren Referenzbildern).
- `image/visual_agent.py` → `VisualAgent` orchestriert: Referenzauswahl → **`_generate_image()`
  ruft `client.images.edit` direkt auf** (Duplikat zu generator) → Slides → Layout → Vision-Review.
- Referenz-Set: bis zu **4 Bilder** (character/body, orthosis/front, location, outfit) werden
  angehängt; gpt-image-1 **mischt** sie.
- Key-Flow: `app.py` liest `OPENAI_API_KEY`/Sidebar → `VisualAgent(api_key, knowledge, settings)`.
  Weitere Aufrufer: `generate_images_step2.py`, `regen_blocked_series.py`.
- `vision_review.py` nutzt separat OpenAI `gpt-5.5` — **bleibt unverändert** (Backend-unabhängig).

## 2. Architektur-Seam (der eigentliche Umbau)

Eine **Backend-Abstraktion** einziehen, damit OpenAI ODER Flux umschaltbar ist:

```
image/backends/base.py      -> ImageBackend (Protocol): 
                                 generate(prompt, reference_paths, size, n) -> bytes
image/backends/openai.py    -> OpenAIImageBackend   (heutiges Verhalten, 1:1 extrahiert)
image/backends/flux.py      -> FluxImageBackend      (NEU: Redux/Kontext)
image/backends/__init__.py  -> get_backend(name, **creds) Factory
```

- `VisualAgent._generate_image()` wird **dünn**: ruft nur noch `self.backend.generate(...)`.
  Die ganze Retry-/Moderation-Sonderlogik wandert in `OpenAIImageBackend`; Flux braucht sie nicht.
- `ImageGenerator` bleibt als OpenAI-Implementierung erhalten (oder wird von `OpenAIImageBackend`
  umschlossen) → Rückwärtskompatibel, kein Bruch für die 3 Aufrufer.

## 3. ⚠️ Kernproblem: Referenz-Mapping (4 Refs → Flux) — REALITÄT geklärt

**Stock-Image `worker-comfyui:5.4.1-flux1-dev` kann nur text→image.** Redux/Kontext
(Bild-Konditionierung) braucht **Zusatzmodelle + Custom-Nodes**, die im Basis-Image NICHT enthalten
sind. Kein fertiges Persona-LoRA vorhanden (HF-User `SvenLuka` = 0 Repos). Optionen, gereiht:

| Option | Wie | Treue Persona | Aufwand |
|---|---|---|---|
| **0) Text-only (sofort)** | Flux.1-dev txt2img; Persona/Orthese/TENA via bestehenden Text-Contract | mittel (kein fixes Gesicht nötig — wir verbergen es ja) | **null** (Endpoint kann es schon) |
| **A) Persona-LoRA** | LoRA auf den vorhandenen Referenzfotos trainieren → im Workflow laden | **hoch** (konsistente Figur/Outfit) | mittel (Training, aber Daten liegen vor) |
| **B) Redux/Kontext** | Custom-Worker-Image o. Network-Volume mit Redux/Kontext-Modell + Nodes | hoch (Stil/Ort/Body) | mittel-hoch (Custom-Image) |

**Empfehlung:** **Phase 2 = Option 0** (beweist sofort, dass das Thema durchläuft). Danach
**Option A (LoRA)** für echte Persona-Treue — die Trainingsdaten sind genau die Referenzfotos, die
schon in `assets/references/` liegen. Redux (B) nur, falls LoRA nicht reicht. Der bestehende
Text-Contract (`prompt_contract.py`, 1:1-TENA-/Orthesen-Regeln) ist **wiederverwendbar**.

## 4. Config / Keys / Dependencies — ENTSCHIEDEN: RunPod

- **Route steht fest: RunPod Serverless** (self-hosted Flux, **kein Vorfilter**). Bereits vorhanden:
  - `RUNPOD_API_KEY` (env, gesetzt) · `RUNPOD_FLUX_ENDPOINT` = `https://api.runpod.ai/v2/<id>` (gesetzt)
  - Health am 2026-06-30: `200`, 1 worker ready/idle, **41 jobs completed** → Endpoint live & erprobt.
- `ProjectSettings` (frozen) erweitern: `image_backend: str = "openai"` (+ env `IMAGE_BACKEND`,
  Default für Flux-Pfad: `runpod_flux`).
- Keine FAL/Replicate/BFL-Creds nötig.
- `app.py` Sidebar: Backend-Dropdown (openai | runpod_flux) + RunPod-Key-Feld (Default aus env).
- `requirements.txt`: **nur** `requests` (oder stdlib `urllib`) für RunPod-HTTP — kein SDK nötig.

### RunPod-API (Serverless)
- Sync:  `POST {endpoint}/runsync`  Body `{"input": { … }}`  → Ergebnis direkt.
- Async: `POST {endpoint}/run` → `{id}`, dann Poll `GET {endpoint}/status/{id}`.
- Header: `Authorization: Bearer $RUNPOD_API_KEY`.
- **Input-Schema GEKLÄRT** (Testlauf + RunPod-GraphQL am 2026-06-30):
  - Endpoint `husky_crimson_hyena` / `bkyqgi2m43kthj`, Image **`runpod/worker-comfyui:5.4.1-flux1-dev`**.
  - Body: `{"input": {"workflow": <ComfyUI API-Graph>, "images": [{"name","image":<base64>}] (optional)}}`.
  - Output: `{"output": {"images": [{"filename","data":<base64>,"type":"base64"}]}}` (Default).
  - Worker hat **FLUX.1-dev** gebacken (txt2img). Redux/Kontext-Modelle/Nodes **nicht** im Stock-Image.

## 5. Moderation-Realität (zur Doku) — bei RunPod self-hosted: **kein Vorfilter** ✅

Alternativen (verworfen, nur zur Doku): fal.ai/Replicate (leichter Filter, teils abschaltbar),
BFL API (eigene Moderation). RunPod erfüllt „eigener Zugang / kein Vorfilter" am saubersten.

## 6. Migrationsschritte (phasenweise, je mit Verifikation)

1. **Seam einziehen** (§2) ohne Verhaltensänderung → bestehende OpenAI-Tests/Runs müssen identisch
   bleiben. *Verif.:* ein Bestands-Run reproduziert byte-nah denselben Prompt-Pfad.
2. **FluxImageBackend** gegen die gewählte Route (§5) implementieren — erstmal **text→image** (ohne
   Referenz). *Verif.:* ein Reveal-Prompt, den OpenAI blockt, läuft bei Flux **durch**.
3. **Referenz-Konditionierung** (§3, Option B/A) andocken. *Verif.:* Persona-/Orthese-/TENA-Treue
   visuell gegen die Referenzen prüfen (Vision-Review läuft ja weiter).
4. **Backend-Umschalter** in `app.py` + Settings + Doku. *Verif.:* Dropdown wechselt Backend live.
5. **Strumpfhosen-/DEN- und `discreet`-Logik** für Flux neu bewerten — die ganzen
   Moderation-Notlösungen (Retry, worn-crop-Ausschluss) sind bei Flux **unnötig** und können für
   Flux-Pfad entschärft werden (mehr erlaubte Sichtbarkeit).

## 7. Risiken / offene Entscheidungen

- **Reference-Mapping** (§3) ist das inhaltliche Risiko — Single-Image-Redux vs. Multi-Ref-Mischung.
- **Hosting-Route** (§5) noch offen → blockiert konkrete Implementierung von §4/§6.2.
- **Kosten/Latenz** je Route unterschiedlich (self-hosted = Fixkosten GPU; hosted = pro Bild).
- **Layout/Overlay-Pipeline** (`layout_composer`) ist Backend-unabhängig → **kein** Umbau nötig.

## 8. Aufwand (grob)

- Seam + OpenAI-Backend extrahieren: ~0,5 Tag
- Flux-Backend (hosted) text→image: ~0,5 Tag · self-hosted: +1–2 Tage Setup
- Referenz-Konditionierung + Tuning: ~1–2 Tage (iterativ, visuell)

---

### Nächster konkreter Block (sobald Route entschieden)
Phase 1 (Seam) + Phase 2 (Flux text→image) — beweist sofort, ob Flux das blockierte Thema
durchlässt, ohne den restlichen Code anzufassen.
