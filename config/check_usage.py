#!/usr/bin/env python3
"""check_usage.py — Live usage dashboard for all CLI AIs.

Reads actual token data from each CLI's local state:
  Claude:  ~/.claude/projects/*/SESSION.jsonl (per-message usage)
           ~/.claude/usage-data/session-meta/ (completed sessions)
           ~/.claude/.credentials.json (plan tier: max_20x)
  Gemini:  ~/.gemini/tmp/*/chats/session-*.json
  Codex:   ~/.codex/state_5.sqlite
  Grok:    ~/ouro/state/usage_tracker.json (manual)
  Ollama:  localhost:11434 (unlimited)

Usage:
  check_usage.py              # Full dashboard
  check_usage.py claude       # Claude detail
  check_usage.py --json       # Machine-readable
"""

import json
import os
import sqlite3
import sys
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path
from collections import defaultdict

HOME = Path.home()
OURO = Path(os.environ.get("OURO_ROOT", HOME / "ouro"))


def claude_usage() -> dict:
    """Read Claude usage from all sources."""
    # Plan info
    plan = "unknown"
    tier = "unknown"
    try:
        creds = json.loads((HOME / ".claude" / ".credentials.json").read_text())
        oauth = creds.get("claudeAiOauth", {})
        plan = oauth.get("subscriptionType", "unknown")
        tier = oauth.get("rateLimitTier", "unknown")
    except Exception:
        pass

    # Current session (active JSONL — real-time data)
    sessions = []
    proj_dir = HOME / ".claude" / "projects"
    if proj_dir.exists():
        for jsonl in proj_dir.rglob("*.jsonl"):
            try:
                mt = jsonl.stat().st_mtime
                if time.time() - mt > 18000:  # skip files older than 5hr
                    continue
                totals = {"input": 0, "output": 0, "cache_write": 0, "cache_read": 0, "msgs": 0}
                model = "?"
                with open(jsonl) as f:
                    for line in f:
                        d = json.loads(line)
                        if d.get("type") == "assistant":
                            msg = d.get("message", {})
                            model = msg.get("model", model)
                            u = msg.get("usage", {})
                            if u:
                                totals["input"] += u.get("input_tokens", 0)
                                totals["output"] += u.get("output_tokens", 0)
                                totals["cache_write"] += u.get("cache_creation_input_tokens", 0)
                                totals["cache_read"] += u.get("cache_read_input_tokens", 0)
                                totals["msgs"] += 1
                if totals["msgs"] > 0:
                    totals["model"] = model
                    totals["session_id"] = jsonl.stem[:8]
                    totals["mtime"] = mt
                    sessions.append(totals)
            except Exception:
                continue

    # Completed session metadata
    meta_dir = HOME / ".claude" / "usage-data" / "session-meta"
    completed_in = completed_out = 0
    if meta_dir.exists():
        cutoff_iso = (datetime.now(timezone.utc) - timedelta(hours=5)).isoformat()
        for f in meta_dir.glob("*.json"):
            try:
                if time.time() - f.stat().st_mtime > 18000:
                    continue
                d = json.loads(f.read_text())
                completed_in += d.get("input_tokens", 0)
                completed_out += d.get("output_tokens", 0)
            except Exception:
                continue

    # Aggregate
    total = {"input": completed_in, "output": completed_out, "cache_write": 0, "cache_read": 0}
    for s in sessions:
        total["input"] += s["input"]
        total["output"] += s["output"]
        total["cache_write"] += s["cache_write"]
        total["cache_read"] += s["cache_read"]

    # Effective tokens (cache_read 90% discounted)
    effective = (total["input"] + total["output"] +
                 total["cache_write"] + int(total["cache_read"] * 0.1))

    return {
        "provider": "claude",
        "plan": plan,
        "tier": tier,
        "sessions_5hr": len(sessions),
        "total": total,
        "effective_tokens": effective,
        "active_sessions": sessions,
    }


def gemini_usage() -> dict:
    """Read Gemini usage from session files."""
    gemini_dir = HOME / ".gemini" / "tmp"
    total_chars = 0
    session_count = 0
    cutoff = time.time() - 3600

    if gemini_dir.exists():
        for sf in gemini_dir.rglob("session-*.json"):
            try:
                if sf.stat().st_mtime < cutoff:
                    continue
                data = json.loads(sf.read_text())
                messages = data.get("messages", data.get("history", []))
                for msg in messages:
                    content = msg.get("content", "")
                    if isinstance(content, list):
                        content = " ".join(p.get("text", "") for p in content if isinstance(p, dict))
                    if isinstance(content, str):
                        total_chars += len(content)
                session_count += 1
            except Exception:
                continue

    return {
        "provider": "gemini",
        "sessions_1hr": session_count,
        "estimated_tokens": total_chars // 4,
    }


def codex_usage() -> dict:
    """Read Codex usage from SQLite."""
    db_path = HOME / ".codex" / "state_5.sqlite"
    if not db_path.exists():
        return {"provider": "codex", "threads_1hr": 0, "estimated_tokens": 0}
    try:
        cutoff = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
        db = sqlite3.connect(str(db_path))
        count = db.execute("SELECT COUNT(*) FROM threads WHERE created_at > ?", (cutoff,)).fetchone()[0]
        return {"provider": "codex", "threads_1hr": count, "estimated_tokens": count * 2000}
    except Exception:
        return {"provider": "codex", "threads_1hr": 0, "estimated_tokens": 0}


def grok_usage() -> dict:
    """Read Grok usage from manual tracker."""
    try:
        state = json.loads((OURO / "state" / "usage_tracker.json").read_text())
        cutoff = time.time() - 3600
        records = state.get("manual_records", {}).get("grok_cli", [])
        records += state.get("manual_records", {}).get("grok_api", [])
        used = sum(r["total"] for r in records if r.get("ts", 0) > cutoff)
        return {"provider": "grok", "tokens_1hr": used}
    except Exception:
        return {"provider": "grok", "tokens_1hr": 0}


def ollama_usage() -> dict:
    """Check Ollama availability."""
    import urllib.request
    try:
        with urllib.request.urlopen("http://localhost:11434/api/tags", timeout=3) as r:
            data = json.loads(r.read())
            models = len(data.get("models", []))
        return {"provider": "ollama", "status": "UP", "models": models, "limit": "unlimited"}
    except Exception:
        return {"provider": "ollama", "status": "DOWN", "models": 0}


def dashboard():
    """Print full usage dashboard."""
    c = claude_usage()
    g = gemini_usage()
    x = codex_usage()
    k = grok_usage()
    o = ollama_usage()

    print("╔══════════════════════════════════════════════════════════╗")
    print("║              CLI AI USAGE DASHBOARD (LIVE)              ║")
    print("╠══════════════════════════════════════════════════════════╣")

    # Claude
    print(f"║ CLAUDE ({c['plan']} / {c['tier']})")
    print(f"║   Sessions (5hr):     {c['sessions_5hr']}")
    print(f"║   Input tokens:       {c['total']['input']:>12,}")
    print(f"║   Output tokens:      {c['total']['output']:>12,}")
    print(f"║   Cache write:        {c['total']['cache_write']:>12,}")
    print(f"║   Cache read:         {c['total']['cache_read']:>12,}  (90% off)")
    print(f"║   Effective tokens:   {c['effective_tokens']:>12,}")
    print(f"║")

    # Gemini
    print(f"║ GEMINI")
    print(f"║   Sessions (1hr):     {g['sessions_1hr']}")
    print(f"║   Est. tokens:        {g['estimated_tokens']:>12,}")
    print(f"║")

    # Codex
    print(f"║ CODEX")
    print(f"║   Threads (1hr):      {x['threads_1hr']}")
    print(f"║   Est. tokens:        {x['estimated_tokens']:>12,}")
    print(f"║")

    # Grok
    print(f"║ GROK")
    print(f"║   Tokens (1hr):       {k['tokens_1hr']:>12,}")
    print(f"║")

    # Ollama
    print(f"║ OLLAMA: {o['status']} ({o.get('models', 0)} models) — {o.get('limit', '?')}")

    print("╚══════════════════════════════════════════════════════════╝")


if __name__ == "__main__":
    args = sys.argv[1:]

    if "--json" in args:
        print(json.dumps({
            "claude": claude_usage(),
            "gemini": gemini_usage(),
            "codex": codex_usage(),
            "grok": grok_usage(),
            "ollama": ollama_usage(),
        }, indent=2, default=str))
    elif args and args[0] == "claude":
        c = claude_usage()
        print(f"Claude {c['plan']} ({c['tier']})")
        print(f"  Effective: {c['effective_tokens']:,} tokens in 5hr window")
        print(f"  Breakdown: in={c['total']['input']:,} out={c['total']['output']:,} cw={c['total']['cache_write']:,} cr={c['total']['cache_read']:,}")
        if c["active_sessions"]:
            print(f"\n  Active sessions:")
            for s in sorted(c["active_sessions"], key=lambda x: -x["mtime"]):
                print(f"    {s['session_id']}: {s['model']} msgs={s['msgs']} in={s['input']:,} out={s['output']:,}")
    else:
        dashboard()
