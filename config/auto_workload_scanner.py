#!/usr/bin/env python3
"""
auto_workload_scanner.py
Self-evolve engine workload scanner for the Ouroboros fracture engine.
Identifies gaps, failures, and system constraints, generating actionable tasks.
"""

import os
import sys
import time
import json
import ast
import subprocess
import argparse
from pathlib import Path

AUTONOMY = {
    'args': '--execute',
    'schedule': 'periodic',
    'period': 10,
    'serial': True,
    'timeout': 300
}

BASE_DIR = Path("~/ouro/ouroboros/projects/fracture-engine").expanduser()
SRC_DIR = BASE_DIR / "src"
TESTS_DIR = BASE_DIR / "tests"
RESULTS_DIR = BASE_DIR / "results"
LOGS_DIR = BASE_DIR / "logs"
STATE_DIR = Path("~/ouro/state").expanduser()
DAEMON_DIR = Path("/tmp/ouro-daemons")

def _safe_read(path: Path) -> str:
    try:
        return path.read_text(encoding='utf-8')
    except Exception:
        return ""

def scan_modules_without_tests():
    issues = []
    if not SRC_DIR.exists(): return issues
    for f in SRC_DIR.rglob("*.py"):
        if f.name == "__init__.py": continue
        rel_path = f.relative_to(SRC_DIR)
        test_file = TESTS_DIR / rel_path.parent / f"test_{f.name}"
        if not test_file.exists():
            issues.append({'type': 'missing_test', 'target': str(f), 'urgency': 3, 'impact': 4})
    return issues

def scan_syntax_errors():
    issues = []
    if not BASE_DIR.exists(): return issues
    for f in BASE_DIR.rglob("*.py"):
        content = _safe_read(f)
        if not content: continue
        try:
            ast.parse(content)
        except SyntaxError as e:
            issues.append({'type': 'syntax_error', 'target': str(f), 'urgency': 5, 'impact': 5, 'msg': str(e)})
    return issues

def scan_stale_results():
    issues = []
    if not RESULTS_DIR.exists(): return issues
    now = time.time()
    for f in RESULTS_DIR.rglob("*"):
        if f.is_file() and (now - f.stat().st_mtime > 7 * 86400):
            issues.append({'type': 'stale_result', 'target': str(f), 'urgency': 2, 'impact': 2})
    return issues

def scan_unused_modules():
    issues = []
    if not SRC_DIR.exists(): return issues
    for f in SRC_DIR.rglob("*.py"):
        content = _safe_read(f)
        if "AUTONOMY" in content and ("'skip': True" in content.replace('"', "'") or '"skip": True' in content):
            issues.append({'type': 'unused_module', 'target': str(f), 'urgency': 1, 'impact': 2})
    return issues

def scan_low_performance_providers():
    issues = []
    p = STATE_DIR / "adaptive_rewards.json"
    if p.exists():
        try:
            data = json.loads(_safe_read(p))
            for provider, reward in data.items():
                if isinstance(reward, (int, float)) and reward < 0.3:
                    issues.append({'type': 'low_perf_provider', 'target': provider, 'urgency': 4, 'impact': 4})
        except Exception:
            pass
    return issues

def scan_disk_pressure():
    issues = []
    for d in [LOGS_DIR, RESULTS_DIR]:
        if not d.exists(): continue
        for f in d.rglob("*"):
            if f.is_file() and f.stat().st_size > 100 * 1024 * 1024:
                issues.append({'type': 'disk_pressure', 'target': str(f), 'urgency': 3, 'impact': 3})
    return issues

def scan_dead_daemons():
    issues = []
    if not DAEMON_DIR.exists(): return issues
    for f in DAEMON_DIR.glob("*.pid"):
        try:
            pid = int(_safe_read(f).strip())
            os.kill(pid, 0)
        except (ValueError, OSError):
            issues.append({'type': 'dead_daemon', 'target': str(f), 'urgency': 5, 'impact': 4})
    return issues

def scan_global_tasks():
    issues = []
    p = STATE_DIR / "global_tasks.jsonl"
    if p.exists():
        for line in _safe_read(p).splitlines():
            if not line.strip(): continue
            try:
                task = json.loads(line)
                if task.get('status') == 'open' and task.get('priority') in ['P0', 'P1']:
                    u = 5 if task['priority'] == 'P0' else 4
                    issues.append({
                        'type': 'global_task', 
                        'target': task.get('id', 'unknown'), 
                        'urgency': u, 
                        'impact': 5, 
                        'action': task.get('action', '')
                    })
            except Exception:
                pass
    return issues

def generate_workloads(max_items=10):
    scanners = [
        scan_modules_without_tests, scan_syntax_errors, scan_stale_results,
        scan_unused_modules, scan_low_performance_providers, scan_disk_pressure,
        scan_dead_daemons, scan_global_tasks
    ]
    
    all_issues = []
    for scan in scanners:
        try:
            all_issues.extend(scan())
        except Exception as e:
            sys.stderr.write(f"Scanner {scan.__name__} failed: {e}\n")

    workloads = []
    seen = set()
    
    for issue in all_issues:
        key = (issue['type'], issue['target'])
        if key in seen: continue
        seen.add(key)
        
        w_type = issue['type']
        target = issue['target']
        urgency = issue.get('urgency', 1)
        impact = issue.get('impact', 1)
        score = urgency * impact
        priority = max(1, min(5, int(score / 5) + 1))
        
        title = f"[{w_type.upper()}] {target}"
        desc = f"Address {w_type} detected in {target}"
        action = ""
        
        if w_type == 'missing_test':
            action = f"python3 -m src.autotask --generate-test {target}"
            desc = "Generate missing unit tests for module."
        elif w_type == 'syntax_error':
            action = f"python3 -m src.autotask --fix-syntax {target}"
            desc = f"Fix syntax error: {issue.get('msg', '')}"
        elif w_type == 'stale_result':
            action = f"rm -f {target}"
            desc = "Remove stale result file to clean up workspace."
        elif w_type == 'unused_module':
            action = f"python3 -m src.autotask --refactor-unused {target}"
        elif w_type == 'low_perf_provider':
            action = f"python3 -m src.autotask --tune-provider {target}"
        elif w_type == 'disk_pressure':
            action = f"truncate -s 0 {target} || rm -f {target}"
        elif w_type == 'dead_daemon':
            action = f"rm -f {target} && systemctl restart ouro-{Path(target).stem} || true"
        elif w_type == 'global_task':
            action = issue.get('action') or f"python3 -m src.autotask --run-task {target}"

        workloads.append({
            'type': w_type,
            'target': target,
            'title': title,
            'description': desc,
            'priority': priority,
            'impact': impact,
            'score': score,
            'action': action
        })
        
    workloads.sort(key=lambda x: x['score'], reverse=True)
    return workloads[:max_items]

def execute_workloads(workloads, max_exec=3, timeout=60):
    executed = []
    for wl in workloads[:max_exec]:
        print(f"Executing Workload: {wl['title']}\nCommand: {wl['action']}")
        try:
            res = subprocess.run(
                wl['action'], shell=True, timeout=timeout, 
                capture_output=True, text=True
            )
            status = "SUCCESS" if res.returncode == 0 else "FAILED"
            print(f"[{status}] CODE:{res.returncode}")
            if res.stdout.strip(): print(f"STDOUT: {res.stdout.strip()[:200]}")
            if res.stderr.strip(): print(f"STDERR: {res.stderr.strip()[:200]}")
            executed.append({'workload': wl, 'status': status, 'code': res.returncode})
        except subprocess.TimeoutExpired:
            print(f"[TIMEOUT] Command exceeded {timeout}s.")
            executed.append({'workload': wl, 'status': 'TIMEOUT', 'code': -1})
        except Exception as e:
            print(f"[ERROR] {e}")
            executed.append({'workload': wl, 'status': 'ERROR', 'code': -2})
        print("-" * 40)
    return executed

def main():
    parser = argparse.ArgumentParser(description="Ouroboros Auto-Workload Scanner")
    parser.add_argument("--scan", action="store_true", help="Run scans and output raw issues")
    parser.add_argument("--generate", action="store_true", help="Generate and output workloads")
    parser.add_argument("--execute", action="store_true", help="Scan, generate and execute top workloads")
    parser.add_argument("--daemon", action="store_true", help="Run in daemon mode (loop every 5min)")
    args = parser.parse_args()

    if args.daemon:
        print("Starting Auto-Workload Scanner Daemon...")
        while True:
            workloads = generate_workloads(max_items=10)
            execute_workloads(workloads, max_exec=3)
            time.sleep(300)
            
    elif args.execute:
        workloads = generate_workloads(max_items=10)
        execute_workloads(workloads, max_exec=3)
        
    elif args.generate:
        workloads = generate_workloads(max_items=10)
        print(json.dumps(workloads, indent=2))
        
    elif args.scan:
        all_issues = []
        scanners = [
            scan_modules_without_tests, scan_syntax_errors, scan_stale_results,
            scan_unused_modules, scan_low_performance_providers, scan_disk_pressure,
            scan_dead_daemons, scan_global_tasks
        ]
        for scan in scanners:
            try:
                all_issues.extend(scan())
            except Exception:
                pass
        print(json.dumps(all_issues, indent=2))
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
