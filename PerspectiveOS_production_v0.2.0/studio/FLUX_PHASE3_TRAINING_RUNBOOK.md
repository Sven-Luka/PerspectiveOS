# Phase 3 — Persona-LoRA Training: Runbook

Schritt-für-Schritt, um die LoRA `perspective_jona_v1` zu trainieren und auf dem
**bereits vorhandenen** Network Volume bereitzustellen. Config:
[`studio/training/ai_toolkit_jona_v1.yaml`](training/ai_toolkit_jona_v1.yaml).

## Fakten (per RunPod-API bestätigt, 2026-06-30)

| | |
|---|---|
| Network Volume | `absent_fuchsia_smelt_volume` (`rd26nueq18`), 50 GB, **EU-SE-1** |
| Endpoint | `husky_crimson_hyena` (`bkyqgi2m43kthj`), GPU `AMPERE_24`, EU-SE-1 |
| Volume angehängt? | **Ja** (`networkVolumeId=rd26nueq18`) — mountet im Worker bei `/workspace` |
| Worker liest LoRAs aus | `/workspace/models/loras/` |

→ Volume anlegen/anhängen **entfällt**. Es fehlt nur Training + Ablage der LoRA.

---

## 0. GPU-Pod starten (EU-SE-1!)

- **Region MUSS EU-SE-1 sein**, sonst lässt sich das Volume nicht mounten.
- Network Volume `absent_fuchsia_smelt_volume` mounten (→ `/workspace`).
- GPU: 24 GB+ reicht (RTX 4090 / A5000 / A40 / L40). Template mit PyTorch/CUDA.
- (Empfehlung: ai-toolkit-Template, falls vorhanden, spart Schritt 2.)

## 1. Volume sichten (was liegt schon da?)

```bash
ls -la /workspace
ls -la /workspace/models 2>/dev/null
ls -la /workspace/models/loras 2>/dev/null
du -sh /workspace/* 2>/dev/null | sort -h
```
Reste eures früheren Trainings (Datensätze/Modelle) hier prüfen, bevor neu geladen wird.

## 2. ai-toolkit installieren (falls nicht im Template)

```bash
cd /workspace
git clone https://github.com/ostris/ai-toolkit.git
cd ai-toolkit && git submodule update --init --recursive
pip install -r requirements.txt
```

## 3. HuggingFace-Login (FLUX.1-dev ist gated)

```bash
export HF_TOKEN=<dein_hf_token>      # aus token_ki.txt; danach rotieren!
huggingface-cli login --token "$HF_TOKEN"
```

## 4. Dataset auf den Pod bringen

Das Dataset liegt lokal in `studio/generated/lora_dataset/jona/` (16 Bilder + .txt).
Ziel auf dem Pod: `/workspace/dataset/jona/`.

**Variante A — runpodctl (empfohlen):**
```bash
# LOKAL (Windows), im Dataset-Ordner:
runpodctl send studio/generated/lora_dataset/jona
# -> gibt einen Code aus. AUF DEM POD:
mkdir -p /workspace/dataset && cd /workspace/dataset
runpodctl receive <code>      # erzeugt ./jona
```
**Variante B:** Ordner als ZIP über das Jupyter-/Web-Terminal des Pods hochladen und nach
`/workspace/dataset/jona/` entpacken.

## 5. Config ablegen & Training starten

```bash
# ai_toolkit_jona_v1.yaml auf den Pod kopieren (z.B. via runpodctl/Jupyter) nach
#   /workspace/ai-toolkit/config/perspective_jona_v1.yaml
cd /workspace/ai-toolkit
python run.py config/perspective_jona_v1.yaml
```
Dauer: ~30–60 Min (2500 Steps, 24 GB). Zwischen-Samples landen in
`/workspace/ai-toolkit-output/perspective_jona_v1/samples/` — dort früh prüfen, ob die
Persona/Orthese sitzt.

## 6. LoRA an die richtige Stelle kopieren

```bash
cp /workspace/ai-toolkit-output/perspective_jona_v1/perspective_jona_v1.safetensors \
   /workspace/models/loras/perspective_jona_v1.safetensors
ls -la /workspace/models/loras/
```

## 7. Pod stoppen

Volume bleibt erhalten (LoRA liegt drauf). **Pod terminieren**, damit keine GPU-Kosten
weiterlaufen. Der Serverless-Endpoint nutzt das Volume unabhängig vom Pod.

---

## 8. Zurück im Studio (mache ich)

```bash
# Backend auf Flux + LoRA:
export IMAGE_BACKEND=runpod_flux
export FLUX_LORA_NAME=perspective_jona_v1.safetensors
export FLUX_LORA_STRENGTH=0.9        # bei Bedarf 0.7–1.0 justieren
```
Dann rendere ich das `poc_blocked`-Motiv neu und vergleiche Orthese/Outfit/Körperbau
gegen die Referenzen. Trigger-Word `j0na` wird automatisch vorangestellt
(siehe `RunPodFluxBackend`).

## Tuning, falls v1 nicht trifft
- Ähnlichkeit zu schwach → `FLUX_LORA_STRENGTH` höher (bis 1.0) oder mehr Steps (3000–3500).
- Überfittet/künstlich → Strength 0.6–0.8 oder Rank 16→8.
- Orthesenseite falsch → Captions schärfen ("on the LEFT leg") / mehr Seiten-/Rückansichten.
