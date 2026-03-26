#!/usr/bin/env python3
"""CLI AI Usage Tracker — LIVE usage from actual session data.

Reads real token counts from each CLI's local state files.
Self-calibrates limits from rate-limit signals.

Sources:
  Claude:  ~/.claude/projects/*/SESSION.jsonl  (usage in assistant messages)
  Gemini:  ~/.gemini/tmp/*/chats/session-*.json (session metadata)
  Codex:   ~/.codex/state_5.sqlite (threads table)
  Grok:    Tracked by this module (no local state file)
  Ollama:  Tracked by this module (local, unlimited)

Usage:
  cli_usage_tracker.py status              # all providers, live data
  cli_usage_tracker.py budget <provider>   # single provider budget
  cli_usage_tracker.py record <provider> <in> <out>  # manual record
"""

import json
import os
import sqlite3
import sys
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path
from collections import defaultdict

OURO = Path(os.environ.get("OURO_ROOT", Path.home() / "ouro"))
HOME = Path.home()
STATE_FILE = OURO / "state" / "usage_tracker.json"

# Rolling window configs per provider
# Claude Max: 5hr window, cache_read tokens are 90% discounted
# Gemini Code Assist: per-minute + per-day limits
# Codex: per-session token budget
WINDOWS = {
    "claude":      {"window_h": 5,  "warn_pct": 0.80, "est_limit": 43_000_000},  # Calibrated: 87% at 37M effective (2026-03-26)
    "gemini":      {"window_h": 1,  "warn_pct": 0.85, "est_limit": 1_000_000},
    "antigravity": {"window_h": 1,  "warn_pct": 0.85, "est_limit": 1_000_000},
    "codex":       {"window_h": 1,  "warn_pct": 0.85, "est_limit": 500_000},
    "grok":        {"window_h": 1,  "warn_pct": 0.90, "est_limit": 5_000_000},  # SuperGrok sub = generous limits
    "ollama":      {"window_h": 1,  "warn_pct": 1.00, "est_limit": 999_999_999},
}


def _load_state() -> dict:
    try:
        return json.loads(STATE_FILE.read_text())
    except Exception:
        return {"manual_records": {}, "rate_limit_hits": {}, "calibrated_limits": {}}


def _save_state(state: dict):
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2))


# ── Live Data Extractors ────────────────────────────────────────────────

def _claude_live_usage(window_hours: float = 5.0) -> dict:
    """Read LIVE Claude token usage from two sources:
    1. ~/.claude/usage-data/session-meta/*.json — completed sessions (authoritative)
    2. ~/.claude/projects/*/SESSION.jsonl — active session transcripts (real-time)
    """
    cutoff = time.time() - (window_hours * 3600)
    totals = defaultdict(int)

    # Source 1: Completed session metadata (authoritative /usage data)
    meta_dir = HOME / ".claude" / "usage-data" / "session-meta"
    if meta_dir.exists():
        for f in meta_dir.glob("*.json"):
            try:
                if f.stat().st_mtime < cutoff:
                    continue
                d = json.loads(f.read_text())
                ts = d.get("start_time", "")
                if ts:
                    try:
                        st = datetime.fromisoformat(ts.replace("Z", "+00:00")).timestamp()
                        if st < cutoff:
                            continue
                    except Exception:
                        pass
                totals["input"] += d.get("input_tokens", 0)
                totals["output"] += d.get("output_tokens", 0)
            except Exception:
                continue

    # Source 2: Active session transcripts (real-time, has cache detail)
    proj_dir = HOME / ".claude" / "projects"
    if proj_dir.exists():
        for jsonl in proj_dir.rglob("*.jsonl"):
            try:
                if jsonl.stat().st_mtime < cutoff:
                    continue
            except OSError:
                continue
            try:
                with open(jsonl) as fh:
                    for line in fh:
                        d = json.loads(line)
                        if d.get("type") != "assistant":
                            continue
                        ts = d.get("timestamp", "")
                        if ts:
                            try:
                                msg_time = datetime.fromisoformat(ts.replace("Z", "+00:00")).timestamp()
                                if msg_time < cutoff:
                                    continue
                            except Exception:
                                pass
                        u = d.get("message", {}).get("usage", {})
                        if u:
                            totals["input"] += u.get("input_tokens", 0)
                            totals["output"] += u.get("output_tokens", 0)
                            totals["cache_read"] += u.get("cache_read_input_tokens", 0)
                            totals["cache_write"] += u.get("cache_creation_input_tokens", 0)
            except Exception:
                continue

    # Effective tokens: input + output + cache_write (full price)
    # cache_read is 90% discounted → counts as 10%
    effective = (totals["input"] + totals["output"] +
                 totals["cache_write"] + int(totals["cache_read"] * 0.1))
    totals["effective"] = effective
    return dict(totals)


def _gemini_live_usage(window_hours: float = 1.0) -> dict:
    """Read LIVE Gemini usage from session files."""
    gemini_dir = HOME / ".gemini" / "tmp"
    if not gemini_dir.exists():
        return {"sessions": 0, "estimated_tokens": 0}

    cutoff = time.time() - (window_hours * 3600)
    total_chars = 0
    session_count = 0

    for session_file in gemini_dir.rglob("session-*.json"):
        try:
            if session_file.stat().st_mtime < cutoff:
                continue
            data = json.loads(session_file.read_text())
            messages = data.get("messages", data.get("history", []))
            for msg in messages:
                content = msg.get("content", msg.get("parts", [{}])[0].get("text", ""))
                if isinstance(content, str):
                    total_chars += len(content)
            session_count += 1
        except Exception:
            continue

    # Estimate tokens: ~4 chars per token
    return {"sessions": session_count, "estimated_tokens": total_chars // 4}


def _codex_live_usage(window_hours: float = 1.0) -> dict:
    """Read LIVE Codex usage from SQLite state."""
    db_path = HOME / ".codex" / "state_5.sqlite"
    if not db_path.exists():
        return {"threads": 0, "estimated_tokens": 0}

    cutoff_iso = (datetime.now(timezone.utc) - timedelta(hours=window_hours)).isoformat()
    try:
        db = sqlite3.connect(str(db_path))
        # Count recent threads
        rows = db.execute(
            "SELECT COUNT(*) FROM threads WHERE created_at > ?",
            (cutoff_iso,)
        ).fetchone()
        thread_count = rows[0] if rows else 0
        # Estimate tokens per thread (~2K average based on typical codex exec)
        return {"threads": thread_count, "estimated_tokens": thread_count * 2000}
    except Exception:
        return {"threads": 0, "estimated_tokens": 0}


def _manual_usage(provider: str, window_hours: float = 1.0) -> int:
    """Get manually recorded usage for providers without local state."""
    state = _load_state()
    cutoff = time.time() - (window_hours * 3600)
    records = state.get("manual_records", {}).get(provider, [])
    return sum(r["total"] for r in records if r.get("ts", 0) > cutoff)


# ── Public API ──────────────────────────────────────────────────────────

def record(provider: str, tokens_in: int, tokens_out: int, was_rate_limited: bool = False):
    """Record a usage event (for providers without local state tracking)."""
    state = _load_state()
    now = time.time()

    if provider not in state["manual_records"]:
        state["manual_records"][provider] = []

    state["manual_records"][provider].append({
        "ts": now, "in": tokens_in, "out": tokens_out,
        "total": tokens_in + tokens_out,
    })

    # Prune old (keep 24h)
    cutoff = now - 86400
    state["manual_records"][provider] = [
        r for r in state["manual_records"][provider] if r["ts"] > cutoff
    ]

    if was_rate_limited:
        hits = state.setdefault("rate_limit_hits", {})
        hits.setdefault(provider, []).append({"ts": now})
        # Self-calibrate: reduce limit by 15%
        cal = state.setdefault("calibrated_limits", {})
        base = _provider_key(provider)
        current = cal.get(base, WINDOWS.get(base, {}).get("est_limit", 100000))
        cal[base] = int(current * 0.85)

    _save_state(state)


def _provider_key(name: str) -> str:
    """Normalize provider name to window key: claude_cli → claude, grok_api → grok."""
    for prefix in ("claude", "gemini", "antigravity", "codex", "grok", "ollama"):
        if name.startswith(prefix):
            return prefix
    return name


def budget(provider: str) -> dict:
    """Return live budget for a provider, reading actual usage data."""
    key = _provider_key(provider)
    cfg = WINDOWS.get(key, {"window_h": 1, "warn_pct": 0.85, "est_limit": 100000})
    window_h = cfg["window_h"]
    warn_pct = cfg["warn_pct"]

    # Get calibrated or default limit
    state = _load_state()
    max_tokens = state.get("calibrated_limits", {}).get(key, cfg["est_limit"])

    # Read LIVE usage
    if key == "claude":
        live = _claude_live_usage(window_h)
        used = live.get("effective", 0)
    elif key in ("gemini", "antigravity"):
        live = _gemini_live_usage(window_h)
        used = live.get("estimated_tokens", 0)
    elif key == "codex":
        live = _codex_live_usage(window_h)
        used = live.get("estimated_tokens", 0)
    elif key == "ollama":
        used = 0  # unlimited
    else:
        used = _manual_usage(provider, window_h)

    # Add any manual records on top
    used += _manual_usage(provider, window_h)

    remaining = max(max_tokens - used, 0)
    pct_used = used / max(max_tokens, 1)

    return {
        "provider": provider,
        "key": key,
        "window_h": window_h,
        "max_tokens": max_tokens,
        "used": used,
        "remaining": remaining,
        "pct_used": round(pct_used, 4),
        "ok": pct_used < warn_pct,
        "warn": pct_used >= warn_pct and remaining > 0,
        "blocked": remaining <= 0,
    }


def should_use(provider: str) -> bool:
    """True if provider has budget and isn't rate-limited."""
    b = budget(provider)
    return b["ok"] and not b["blocked"]


def status() -> list[dict]:
    """Live status across all providers."""
    providers = ["claude", "gemini", "antigravity", "codex", "grok", "ollama"]
    return [budget(p) for p in providers]


if __name__ == "__main__":
    args = sys.argv[1:]
    is_json = "--json" in args

    if not args or args[0] == "status":
        results = status()
        if is_json:
            print(json.dumps(results, indent=2))
        else:
            print(f"{'Provider':<15} {'Window':>7} {'Used':>12} {'Limit':>12} {'Remaining':>12} {'%Used':>7} {'Status':>8}")
            print("-" * 78)
            for r in results:
                st = "BLOCKED" if r["blocked"] else ("WARN" if r["warn"] else "OK")
                print(f"{r['provider']:<15} {r['window_h']:>5.0f}h {r['used']:>12,} {r['max_tokens']:>12,} {r['remaining']:>12,} {r['pct_used']:>6.1%} {st:>8}")
    elif args[0] == "budget" and len(args) >= 2:
        b = budget(args[1])
        if is_json:
            print(json.dumps(b, indent=2))
        else:
            st = "BLOCKED" if b["blocked"] else ("WARN" if b["warn"] else "OK")
            print(f"{b['provider']}: {b['remaining']:,} remaining of {b['max_tokens']:,} ({b['pct_used']:.1%} used) [{st}]")
    elif args[0] == "record" and len(args) >= 4:
        record(args[1], int(args[2]), int(args[3]), "--rate-limited" in args)
    elif args[0] == "claude-detail":
        live = _claude_live_usage(5.0)
        print(f"Claude 5hr window:")
        print(f"  Input tokens:      {live.get('input', 0):>12,}")
        print(f"  Output tokens:     {live.get('output', 0):>12,}")
        print(f"  Cache write:       {live.get('cache_write', 0):>12,}")
        print(f"  Cache read:        {live.get('cache_read', 0):>12,}  (90% discounted)")
        print(f"  Effective tokens:  {live.get('effective', 0):>12,}")
    else:
        print(__doc__)
