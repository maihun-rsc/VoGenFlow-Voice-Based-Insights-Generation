#!/usr/bin/env python3
"""
run_desktop.py
Standalone launcher for the VoGenFlow Modernized Desktop Application.
Features graceful headless detection, theme selection, and automated dry-run verification.
"""

import argparse
import logging
import os
import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("vogenflow.launcher")


def is_headless_environment() -> bool:
    """Detect if the current environment cannot render a graphical display."""
    if os.environ.get("QT_QPA_PLATFORM") == "offscreen":
        return True
    if os.environ.get("CI") == "true" or os.environ.get("GITHUB_ACTIONS") == "true":
        return True
    if sys.platform.startswith("linux"):
        if not os.environ.get("DISPLAY") and not os.environ.get("WAYLAND_DISPLAY"):
            return True
    return False


def run_headless_dry_run(theme: str = "onyx", test_docx: bool = True) -> int:
    """Execute offscreen validation of the desktop client without popping a GUI window."""
    logger.info("Initializing VoGenFlow Desktop in Graceful Headless / Dry-Run Mode...")
    from PyQt6.QtWidgets import QApplication
    from src.ui.main_window import MainWindow

    app_args = sys.argv + ["-platform", "offscreen"]
    app = QApplication.instance() or QApplication(app_args)

    logger.info("Instantiating MainWindow (Theme: %s)...", theme)
    window = MainWindow(default_theme=theme, default_backend="auto")

    # Verification 1: Title and Core Dimensions
    assert "VoGenFlow" in window.windowTitle(), f"Unexpected window title: {window.windowTitle()}"
    logger.info("✓ Window title verified: '%s'", window.windowTitle())

    # Verification 2: 4 Navigation Views
    assert window.main_nav_tabs.count() == 4, f"Expected 4 navigation tabs, found {window.main_nav_tabs.count()}"
    logger.info("✓ 4 Workspace navigation tabs initialized successfully.")

    # Verification 3: 6 Council Agent Cards
    expected_agents = ["pm_agent", "architect_agent", "ui_agent", "systems_agent", "agile_agent", "diff_agent"]
    for agent_key in expected_agents:
        assert agent_key in window.agent_cards, f"Missing agent card for {agent_key}"
    logger.info("✓ All 6 Council Agent dossier cards verified (PM, Architect, UI/UX, Lifecycle, Agile, Delta Refiner).")

    # Verification 4: Theme Toggle
    window.set_theme("vellum")
    assert window.current_theme == "vellum", "Failed to switch to Vellum Light theme"
    window.set_theme("onyx")
    assert window.current_theme == "onyx", "Failed to switch back to Onyx Black theme"
    logger.info("✓ Dynamic theme engine verified: Onyx True Black <-> Vellum Luxury Light.")

    # Verification 5: Load Mock Artifacts & ProjectIR
    mock_artifacts = {
        "PRD.md": "# Global Payments Gateway PRD\n\n## 1. Problem Statement\nHigh-throughput settlement system.",
        "Architecture.md": "# System Architecture\n\n## PostgreSQL 16 Table DDL\n```sql\nCREATE TABLE accounts (id UUID PRIMARY KEY);\n```",
        "Flow.md": "# Sequence Flows\n\n```mermaid\nsequenceDiagram\nClient->>Gateway: POST /tx\n```",
        "tasks.md": "# Phased Delivery Tasks\n\n- [ ] M1: Database Models\n- [ ] M2: Core Engine",
        "design.md": "# Monolith Design System\n\n- Onyx: #000000\n- Gold: #D4AF37",
        "master_execution_bundle.md": "# Master Execution Bundle\nAutonomous downstream contract."
    }
    mock_project_ir = {
        "project_name": "Global Payments & Settlement Gateway",
        "tagline": "Real-time ledger with partitioned PostgreSQL 16",
        "executive_summary": "Autonomous cloud financial infrastructure.",
        "requirements": [
            {"id": "REQ-001", "priority": "P0", "title": "Ledger Ingestion", "acceptance_criteria": ["Sub-50ms latency"]}
        ],
        "non_functional_slas": [
            {"metric": "P95 Latency", "target": "< 25ms", "verification_method": "k6 load test"}
        ],
        "security_threat_matrix": [
            {"threat_category": "Tampering", "threat_description": "Replay attacks", "mitigation": "HMAC-SHA256 nonces"}
        ],
        "architecture": {
            "database_ddl": "CREATE TABLE ledger_entries (id UUID PRIMARY KEY);",
            "database_models": [],
            "api_contracts": []
        },
        "lifecycle": {
            "failure_recovery_matrix": [
                {"component": "Redis Leader", "detection_sla": "< 1s", "recovery_mechanism": "Sentinel failover"}
            ]
        }
    }
    window.load_mock_artifacts(mock_artifacts, project_ir=mock_project_ir)
    logger.info("✓ Artifacts and ProjectIR successfully parsed into Specification Studio & AST Inspector.")

    # Verification 6: Test Client-Side Word (.docx) Export
    if test_docx:
        temp_dir = PROJECT_ROOT / "temp_audio"
        temp_dir.mkdir(exist_ok=True)
        docx_test_path = str(temp_dir / "Headless_Test_Export.docx")
        exported = window.export_to_docx(target_path=docx_test_path)
        assert exported and os.path.exists(exported), "Word export failed to create file."
        file_size = os.path.getsize(exported)
        assert file_size > 1000, f"Exported .docx is unexpectedly small: {file_size} bytes"
        logger.info("✓ 1-Click Client-Side Word (.docx) export verified successfully (%d bytes).", file_size)
        try:
            os.remove(exported)
        except Exception:
            pass

    logger.info("=" * 60)
    logger.info(" VoGenFlow Desktop Headless Dry-Run PASSED with 100% SUCCESS.")
    logger.info("=" * 60)
    return 0


def main():
    parser = argparse.ArgumentParser(description="VoGenFlow Modernized Desktop Application Launcher")
    parser.add_argument("--headless", action="store_true", help="Run in headless offscreen mode")
    parser.add_argument("--dry-run", action="store_true", help="Execute self-test dry-run and exit")
    parser.add_argument("--theme", choices=["onyx", "vellum"], default="onyx", help="Initial palette theme (default: onyx)")
    parser.add_argument("--backend", choices=["auto", "http", "in_process"], default="auto", help="Backend connection mode")
    parser.add_argument("--export-docx", metavar="OUTPUT_PATH", help="Export sample specifications to .docx and exit")

    args = parser.parse_args()

    # Direct export shortcut
    if args.export_docx:
        from src.export_service import ExportService
        sample_artifacts = {
            "PRD.md": "# Sample PRD\nAutonomous system requirements.",
            "Architecture.md": "# System Architecture\nPostgreSQL 16 schemas.",
            "Flow.md": "# Sequence Flows\nRequest lifecycles.",
            "tasks.md": "# Tasks\n- [ ] Milestone 1",
            "design.md": "# Design Tokens\nMonolith Onyx."
        }
        out = ExportService.export_to_docx(sample_artifacts, args.export_docx)
        print(f"Exported .docx to: {out}")
        return 0

    # Auto-detect headless environment
    headless = args.headless or args.dry_run or is_headless_environment()

    if headless:
        return run_headless_dry_run(theme=args.theme)

    # Launch interactive GUI client
    from PyQt6.QtWidgets import QApplication
    from src.ui.main_window import MainWindow

    app = QApplication(sys.argv)
    app.setApplicationName("VoGenFlow")

    window = MainWindow(default_theme=args.theme, default_backend=args.backend)
    window.show()

    logger.info("VoGenFlow Desktop Application active. Entering Qt event loop.")
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
