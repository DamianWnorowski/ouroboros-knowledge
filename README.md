# Ouroboros Knowledge Base

All research, system maps, prompts, fracture results, diagrams, and session artifacts from the Ouroboros AI system. Single source of truth for cross-machine sync.

## Structure

```
research/          — 9 elite research papers (Gemini+Ollama generated, zero Claude tokens)
system-map/        — Full architecture map (7 parallel agents, 1.4MB output)
  agents/          — Per-system detailed maps (fracture-engine, CTE, omni-pipeline, dotD, hyperelite, infra, observer)
fractures/         — Fracture analysis results (16 vectors × 10 frames)
diagrams/          — Architecture diagrams (NOELLE ALEK cognitive agent)
prompts/           — Analysis frameworks (Eternal Patterns 10-lens)
acp-results/       — Antigravity ACP swarm outputs (35 parallel agent results)
tasks/             — Global task tracker (JSONL) + master TODO
treasures/         — Per-session treasure manifests with full change logs
config/            — Key configs, utility scripts, architecture code
memory/            — Feedback memories + provider maps
polysync/          — Cross-machine node registrations (Linux + Windows)
```

## Session D13 Stats (2026-03-26)

- **15 auto-improvements** implemented and committed
- **9 research papers** generated via Gemini+Ollama
- **7 parallel agents** mapped full system (1.4MB structured output)
- **4 ACP Gemini swarm tasks** completed
- **31 global tasks** tracked (12 done, 19 open)
- **10+ LLM providers** in adaptive omni-pipeline
- **187x juice multiplier** on Claude Max 20x ($37K API-equiv from $200/mo)
- **3 repos cloned** from other PC (dotD, hyperelite-sdk, gemini-cli-main)

## Cross-Machine Sync

Both PCs sync via:
1. `git pull` on this repo — gets all artifacts
2. `git pull` on [dotD](https://github.com/DamianWnorowski/dotD) — PolySYNC config
3. GitHub Issues — master TODO on [fracture-engine#1](https://github.com/DamianWnorowski/fracture-engine/issues/1) + [CTE#1](https://github.com/DamianWnorowski/cognitive-trace-engine/issues/1)

## Related Repos

| Repo | Purpose |
|------|---------|
| [fracture-engine](https://github.com/DamianWnorowski/fracture-engine) | 42K LOC self-evolving cognitive stress-test engine |
| [cognitive-trace-engine](https://github.com/DamianWnorowski/cognitive-trace-engine) | 230K LOC autonomous brain + DPO pipeline |
| [hyperelite-sdk](https://github.com/DamianWnorowski/hyperelite-sdk) | Multi-provider agent runtime, tournament evolution |
| [dotD](https://github.com/DamianWnorowski/dotD) | Elite CLI config, 34 MCP servers, PolySYNC |
| [omega](https://github.com/DamianWnorowski/omega) | LLM training pipeline (Rust, 55K LOC) |
| [ouroboros-rs](https://github.com/DamianWnorowski/ouroboros-rs) | Rust workspace (17 crates) |
