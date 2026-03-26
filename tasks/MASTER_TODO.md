## Global Master TODO — Ouroboros System
**12/31 done | 19 open**
Source: `~/ouro/state/global_tasks.jsonl`

### P0 (2 tasks)
- [ ] **#12** [fix] Restore Omega source from .git.backup
  > Mass secret replacement corrupted 6000+ .rs files. Omega can't compile. Restore from .git.backup, verify build, repush.
- [ ] **#13** [fix] Fix 118 corrupted bin/ scripts *(blocked by #12)*
  > Mass REDACTED_SECRET replacement corrupted 118 scripts in bin/. Restore from backup.

### P1 (6 tasks)
- [ ] **#1** [infrastructure] Activate $1K Google Cloud credits
  > gcloud auth login → set project → enable Vertex AI API. $1K credits = ~666M tokens Gemini 2.0 Flash.
- [ ] **#2** [infrastructure] Export GOOGLE_API_KEY from aistudio.google.com
  > google-genai 1.65.0 already installed. Omni-pipeline auto-activates google_ai provider when key is set. Free 1M tokens/day.
- [ ] **#6** [build] Wire real implementations into hyper_poly_swap.py slots
  > Current file has stub implementations. Wire actual SQLite/Qdrant/Redis storage, actual CLI agents (Claude/Gemini/Codex/Grok), actual SearXNG search. C
- [ ] **#14** [fix] Repush GitHub repos after restoration *(blocked by #12, #13)*
  > 4 repos were pushed with corrupted source. Need to force-push clean versions after restore.
- [ ] **#23** [build] Build auto-usage-optimizer daemon *(blocked by #3, #6)*
  > Daemon that continuously rebalances across providers based on live budgets. When Claude hits 80%, auto-routes to Gemini/Ollama. When Gemini hits RPM l
- [ ] **#26** [build] Calibrate Claude usage tracker against /usage
  > Current 43M limit estimate conflicts with 448M effective seen in check_usage.py. Multiple parallel sessions (Gemini-spawned) inflate numbers. Need to 

### P2 (7 tasks)
- [ ] **#5** [fix] Fix Grok API credits (429 exhausted)
  > xAI API credits exhausted on team 2dd5cee8-... SuperGrok CLI sub is separate from API credits. Need to purchase API credits or wait for refill.
- [ ] **#7** [infrastructure] Spin up vLLM in Docker
  > Docker is running. vLLM is 2-4x faster than Ollama for batch inference. docker run vllm/vllm-openai with local models.
- [ ] **#8** [infrastructure] Wire Kilo Code extension as compute provider
  > kilocode.kilo-code-5.11.0 installed in Antigravity. Free autonomous AI coding agent with its own quotas. Can edit files, run terminal, execute code.
- [ ] **#9** [infrastructure] Wire ChatGPT/Codex extension in Antigravity
  > openai.chatgpt-26.323.20928 installed in Antigravity. 'Included in ChatGPT Plus, Pro, Business'. Separate quota from codex CLI.
- [ ] **#17** [fix] CTE→Omega DPO synapse — automate post_pretrain_pipeline.sh *(blocked by #12)*
  > Synapse documented as PARTIAL. harvest runs but post_pretrain_pipeline.sh is manual-only. With DPO velocity=0 for 8+ hours, reactive trigger never fir
- [ ] **#21** [build] Deploy AI endpoints on Vercel/Netlify (free compute)
  > Both have MCP servers active. Vercel: AI SDK + serverless + edge. Netlify: 125K function invocations/mo free. Can deploy inference endpoints.
- [ ] **#22** [build] Wire Supabase edge functions + pgvector
  > Supabase MCP configured. Free PostgreSQL + pgvector (supplement Qdrant) + edge functions (Deno serverless compute) + realtime CDC.

### P3 (4 tasks)
- [ ] **#10** [infrastructure] Set up GitHub Actions for batch inference
  > GitHub account DamianWnorowski. 2000 min/mo free compute. Run Ollama in Docker for batch DPO generation offloaded to cloud.
- [ ] **#11** [infrastructure] Check GitHub Copilot availability
  > gh CLI installed and authenticated. Check if Copilot is included with account plan. gh copilot suggest/explain for quick tasks.
- [ ] **#19** [research] Integrate NOELLE ALEK architecture with Ouroboros
  > User shared architecture diagram (photo.png). Full cognitive agent system: Perception Engine, Security & Autonomy, Interface Systems, Core reasoning. 
- [ ] **#20** [research] View Grok shared link from user
  > User shared https://grok.com/share/c2hhcmQtMw_22ffd326-40e4-402c-93e4-7896b4e14df4 — never viewed. Need to fetch and integrate.

### Done
- [x] **#3** Wire Redis as LLM response cache (2026-03-26)
- [x] **#4** Fix Grok CLI (410 live_search deprecation) (2026-03-26)
- [x] **#15** AION equilibrium false positive — add weighted quorum (2026-03-26)
- [x] **#16** Knowledge graph write lock — prevent concurrent clobber (2026-03-26)
- [x] **#18** Add source field to ALL DPO pairs (2026-03-26)
- [x] **#24** Autotask queue drain mechanism (2026-03-26)
- [x] **#25** Disk pressure monitoring in reactive engine (2026-03-26)
- [x] **#27** Fail-deadly Ollama fallback in smart_llm_call (?)
- [x] **#28** Tier 0 immutable axioms in temporal_memory (?)
- [x] **#29** Speed+locality bonus in UCB1 reward function (?)
- [x] **#30** Knowledge graph file lock (fcntl.flock) (?)
- [x] **#31** Polynested preset module (?)

---
*Auto-generated from session D13 (2026-03-26)*
