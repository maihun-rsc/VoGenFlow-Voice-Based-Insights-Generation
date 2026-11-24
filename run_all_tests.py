#!/usr/bin/env python3
"""
run_all_tests.py
Unified 4-Tier Test Runner for Vo-Gen-Flow 2.0.

Aligned with BUILD.md 4-Tier Real Execution Testing Framework:
- Tier 1: Deterministic Unit & Contract Tests (tests/unit)
- Tier 2: Real Integration & WebSocket Streams (tests/integration)
- Tier 3: Security, DAST & Vulnerability Tests (tests/security)
- Tier 4: Headless Browser Viewports & E2E Simulation (tests/e2e)
- Repository Baseline Suite (tests/test_*.py root tests)

Executes all suites, aggregates granular metrics, and exits 0 on 100% pass.
"""

import os
import sys
import time
import argparse
import subprocess
from typing import Dict, Any, List, Optional
from pathlib import Path

# Fix Windows console UTF-8 output if supported
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# ANSI Color Codes
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
GOLD = "\033[33m"
BOLD = "\033[1m"
RESET = "\033[0m"


TIER_CONFIG = {
    "tier1": {
        "name": "Tier 1: Unit & Contract Tests",
        "description": "In-memory deterministic models, router math, prompt compiler",
        "path": "tests/unit",
        "args": ["tests/unit"]
    },
    "tier2": {
        "name": "Tier 2: Integration & Contract Tests",
        "description": "FastAPI REST endpoints, Advisory fallback, WebSocket streaming",
        "path": "tests/integration",
        "args": ["tests/integration"]
    },
    "tier3": {
        "name": "Tier 3: Security & Vulnerability Tests",
        "description": "Path traversal probes, CORS security, AST sanitization, Secret audit",
        "path": "tests/security",
        "args": ["tests/security"]
    },
    "tier4": {
        "name": "Tier 4: UI & Viewport E2E Simulation",
        "description": "Playwright headless multi-viewport 1920/1440/375/414px 0 overflow",
        "path": "tests/e2e",
        "args": ["tests/e2e"]
    },
    "root_baseline": {
        "name": "Repository Baseline Test Suite",
        "description": "Existing repository unit & stress regression benchmarks",
        "path": "tests/*.py",
        "args": [
            "tests/test_adversarial_injection.py",
            "tests/test_api.py",
            "tests/test_backend_robustness.py",
            "tests/test_council.py",
            "tests/test_desktop_app.py",
            "tests/test_desktop_gui_simulation.py",
            "tests/test_dispatcher.py",
            "tests/test_knowledge_db.py",
            "tests/test_mcp_e2e.py",
            "tests/test_mcp_server.py",
            "tests/test_rag.py",
            "tests/test_rag_benchmark.py",
            "tests/test_rag_guardrails.py",
            "tests/test_recorder.py",
            "tests/test_router.py",
            "tests/test_security_pentest.py",
            "tests/test_sqlite_store.py",
            "tests/test_stress_m1.py",
            "tests/test_stt.py",
            "tests/test_trial_quota.py"
        ]
    }
}


def run_tier(tier_key: str, verbose: bool = False) -> Dict[str, Any]:
    """Execute a single test tier via pytest and parse results."""
    conf = TIER_CONFIG[tier_key]
    name = conf["name"]
    args = conf["args"]

    print(f"\n{BOLD}{GOLD}>>> Executing {name}...{RESET}")
    print(f"{CYAN}    Description: {conf['description']}{RESET}")

    env = os.environ.copy()
    env["PYTHONPATH"] = str(Path.cwd().resolve())

    cmd = [sys.executable, "-m", "pytest"] + args + ["-v"]

    start_time = time.time()
    result = subprocess.run(cmd, env=env, capture_output=True, text=True, encoding="utf-8", errors="replace")
    duration = time.time() - start_time

    output = result.stdout + "\n" + result.stderr

    # Parse passed / failed / collected counts from pytest output
    passed_count = 0
    failed_count = 0
    total_collected = 0

    import re
    col_match = re.search(r"collected\s+(\d+)\s+items", output)
    if col_match:
        total_collected = int(col_match.group(1))

    pass_match = re.search(r"(\d+)\s+passed", output)
    if pass_match:
        passed_count = int(pass_match.group(1))

    fail_match = re.search(r"(\d+)\s+failed", output)
    if fail_match:
        failed_count = int(fail_match.group(1))

    error_match = re.search(r"(\d+)\s+error", output)
    if error_match:
        failed_count += int(error_match.group(1))

    if result.returncode == 0 and failed_count == 0 and passed_count == 0 and total_collected > 0:
        passed_count = total_collected

    status = "PASSED" if result.returncode == 0 and failed_count == 0 else "FAILED"
    status_color = GREEN if status == "PASSED" else RED

    print(f"    {status_color}[{status}]{RESET} Passed: {passed_count} | Failed: {failed_count} | Duration: {duration:.2f}s")
    if result.returncode != 0:
        print(f"\n{RED}--- Failure Output for {name} ---{RESET}")
        print(output[-1200:])

    return {
        "tier_key": tier_key,
        "name": name,
        "status": status,
        "passed": passed_count,
        "failed": failed_count,
        "duration": duration,
        "exit_code": result.returncode,
        "output": output
    }


def main():
    parser = argparse.ArgumentParser(description="Vo-Gen-Flow 2.0 4-Tier Real Execution Test Runner")
    parser.add_argument("--tier", choices=["1", "2", "3", "4", "all", "root"], default="all",
                        help="Select tier to execute (1: Unit, 2: Integration, 3: Security, 4: E2E, root: Baseline, all: Complete)")
    parser.add_argument("--skip-e2e", "--fast", action="store_true",
                        help="Skip Tier 4 browser viewport tests for fast execution")
    parser.add_argument("--skip-baseline", action="store_true",
                        help="Skip existing repository root tests")
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="Enable verbose pytest logging")

    args = parser.parse_args()

    # Determine tiers to run
    tiers_to_run = []
    if args.tier == "1":
        tiers_to_run = ["tier1"]
    elif args.tier == "2":
        tiers_to_run = ["tier2"]
    elif args.tier == "3":
        tiers_to_run = ["tier3"]
    elif args.tier == "4":
        tiers_to_run = ["tier4"]
    elif args.tier == "root":
        tiers_to_run = ["root_baseline"]
    else:  # all
        tiers_to_run = ["tier1", "tier2", "tier3"]
        if not args.skip_e2e:
            tiers_to_run.append("tier4")
        if not args.skip_baseline:
            tiers_to_run.append("root_baseline")

    print(f"{BOLD}{GOLD}")
    print("================================================================================")
    print("             Vo-Gen-Flow 2.0 // 4-Tier Real Execution Test Suite                ")
    print("================================================================================")
    print(f"{RESET}")
    print(f"  Working Directory: {Path.cwd().resolve()}")
    print(f"  Python Version:    {sys.version.split()[0]}")
    print(f"  Target Tiers:      {', '.join(tiers_to_run)}")
    print("--------------------------------------------------------------------------------")

    total_start = time.time()
    results = []

    for t_key in tiers_to_run:
        res = run_tier(t_key, verbose=args.verbose)
        results.append(res)

    total_duration = time.time() - total_start
    total_passed = sum(r["passed"] for r in results)
    total_failed = sum(r["failed"] for r in results)
    all_passed = all(r["status"] == "PASSED" for r in results)

    # Print Summary Table
    print(f"\n{BOLD}")
    print("================================================================================")
    print("                               EXECUTION SUMMARY                                ")
    print("================================================================================")
    print(f"{'Tier':<38} | {'Passed':<8} | {'Failed':<8} | {'Status':<10} | {'Duration'}")
    print("--------------------------------------------------------------------------------")

    for r in results:
        stat_color = GREEN if r["status"] == "PASSED" else RED
        stat_str = f"{stat_color}{r['status']:<10}{RESET}"
        print(f"{r['name']:<38} | {r['passed']:<8} | {r['failed']:<8} | {stat_str} | {r['duration']:.2f}s")

    print("--------------------------------------------------------------------------------")
    overall_color = GREEN if all_passed else RED
    overall_status = f"{overall_color}{'100% PASS' if all_passed else 'FAILURES DETECTED'}{RESET}"
    print(f"{'TOTAL METRICS':<38} | {total_passed:<8} | {total_failed:<8} | {overall_status:<10} | {total_duration:.2f}s")
    print(f"================================================================================{RESET}\n")

    if all_passed:
        print(f"{GREEN}{BOLD}✓ ALL 4-TIER ANTI-VIBE VERIFICATION TESTS PASSED SUCCESSFULLY!{RESET}\n")
        sys.exit(0)
    else:
        print(f"{RED}{BOLD}✗ VERIFICATION SUITE FAILED - REVIEW LOGS ABOVE FOR DETAILS.{RESET}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
