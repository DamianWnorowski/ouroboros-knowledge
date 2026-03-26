---
name: omni_pipeline_providers
description: All AI compute providers, their limits, and subscription details for the omni-pipeline
type: reference
---

# Omni-Pipeline Provider Map

## Active Subscriptions
- **Claude Max 20x** — $200/mo, opus-4-6, ~43M effective/5hr window (calibrated 2026-03-26)
- **SuperGrok** — included sub, grok-4-latest, API credits exhausted (429), CLI broken (410 live_search)
- **Gemini Code Assist** — $0 OAuth, gemini-3.1-pro-preview, unlimited via antigravity_direct.py
- **Codex (OpenAI)** — $0 free tier, gpt-4o, codex exec --full-auto
- **Google Cloud** — $1K credits, Vertex AI Gemini, gcloud installed but no project set
- **ChatGPT Plus/Pro** — OpenAI extension in Antigravity, separate quota from Codex CLI

## Local Infrastructure
- **Ollama** — 16 models, dual RTX GPU, unlimited
- **Qdrant** — 12 collections, 26GB index, Docker
- **SearXNG** — 21+ search engines, Docker
- **Redis** — RUNNING, untapped for LLM caching
- **Open-WebUI** — Ollama frontend, Docker

## Omni-Pipeline Location
- Core: `~/ouro/ouroboros/projects/fracture-engine/src/__init__.py` → `smart_llm_call()`
- Usage tracker: `~/ouro/bin/py/cli_usage_tracker.py`
- Dashboard: `~/ouro/bin/py/check_usage.py`

## Key Gotchas
- Grok API key at ~/ouro/config/ai-configs/grok/user-settings.json → 429 credits exhausted
- Grok CLI (@vibe-kit/grok-cli) → 410 live_search deprecated bug
- Claude -p blocked when CLAUDECODE=1 → omni-pipeline unsets it
- Google AI Studio needs GOOGLE_API_KEY from aistudio.google.com
- Claude effective tokens = input + output + cache_write + (cache_read * 0.10)
