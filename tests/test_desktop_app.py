"""
Tests for VoGenFlow Modernized Desktop Application (PyQt6)
Verifies window initialization, Monolith luxury aesthetics (Onyx Black & Vellum Light),
6-Seat Council Chamber viewer, Multi-Tab Specification Studio with Markdown preview,
ProjectIR Telemetry & Schema Inspector, and 1-Click Client-Side Word (.docx) Export.
"""

import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Dict, Any

import pytest
import docx
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.ui.main_window import MainWindow, DropZoneWidget, CouncilAgentCard
from src.ui.audio_visualizer import AudioVisualizer
from src.export_service import ExportService
from run_desktop import run_headless_dry_run


@pytest.fixture(scope="session")
def qapp():
    """Session-level offscreen QApplication fixture."""
    app = QApplication.instance()
    if app is None:
        app = QApplication(["pytest", "-platform", "offscreen"])
    return app


@pytest.fixture
def sample_artifacts() -> Dict[str, str]:
    """Sample generated council artifacts for test suite."""
    return {
        "PRD.md": (
            "# Global Payments Gateway PRD\n\n"
            "## 1. Problem Statement\n"
            "High-throughput multi-currency settlement system with strict ACID invariants.\n\n"
            "## 2. Target Personas\n"
            "- Payment Operations Specialist\n"
            "- Treasury Engineer\n\n"
            "## 3. Non-Functional SLAs Table\n"
            "| Metric | Target | Verification |\n"
            "|---|---|---|\n"
            "| P95 Latency | < 25ms | k6 load test |\n"
            "| Availability | 99.999% | Pingdom probe |\n"
        ),
        "Architecture.md": (
            "# System Architecture & PostgreSQL DDL\n\n"
            "```mermaid\n"
            "flowchart TD\n"
            "Client --> Gateway[FastAPI Ingress]\n"
            "Gateway --> Engine[Settlement Engine]\n"
            "Engine --> DB[(PostgreSQL 16 Partitioned)]\n"
            "```\n\n"
            "## PostgreSQL 16 Table DDL\n"
            "```sql\n"
            "CREATE TABLE accounts (\n"
            "    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),\n"
            "    tenant_id UUID NOT NULL,\n"
            "    balance NUMERIC(18, 4) NOT NULL DEFAULT 0.0000,\n"
            "    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()\n"
            ");\n"
            "ALTER TABLE accounts ENABLE ROW LEVEL SECURITY;\n"
            "```"
        ),
        "Flow.md": (
            "# Lifecycle Sequence Flows & Failure Recovery\n\n"
            "```mermaid\n"
            "sequenceDiagram\n"
            "Client->>Gateway: POST /v1/transactions\n"
            "Gateway->>Engine: Reserve Funds\n"
            "Engine->>DB: Ledger Commit\n"
            "DB-->>Client: 201 Created (Tx ID)\n"
            "```\n\n"
            "## Operational Failure Recovery Matrix\n"
            "| Component | Detection SLA | Recovery Mechanism |\n"
            "|---|---|---|\n"
            "| Redis Leader | < 1s | Sentinel automated failover |\n"
            "| Worker Pod | < 3s | Kubernetes liveness probe restart |\n"
        ),
        "tasks.md": (
            "# Phased Engineering Delivery Checklists\n\n"
            "## Milestone 1: Domain Models & Database Schemas\n"
            "- [ ] Create `src/models/account.py`\n"
            "- [ ] Run `pytest tests/test_db_models.py`\n\n"
            "## Milestone 2: Settlement Engine\n"
            "- [ ] Implement two-phase commit lock\n"
        ),
        "design.md": (
            "# Monolith Luxury Reductionist Design System\n\n"
            "## Palette Tokens\n"
            "- Onyx Black: `#000000`\n"
            "- Brushed Gold: `#D4AF37`\n"
            "- Vellum Light: `#F7F6F2`\n"
        ),
        "master_execution_bundle.md": (
            "# Master Execution Bundle\n"
            "Autonomous downstream contract for coding agents.\n"
        )
    }


@pytest.fixture
def sample_project_ir() -> Dict[str, Any]:
    """Sample ProjectIR data dictionary."""
    return {
        "project_name": "Global Payments & Settlement Gateway",
        "tagline": "High-velocity multi-currency distributed ledger",
        "executive_summary": "Autonomous cloud financial infrastructure with zero downtime.",
        "target_personas": [
            {"name": "Alice", "role": "Treasury Lead", "pain_points": ["Slow batch settlement"], "needs": ["Sub-second clearing"]}
        ],
        "requirements": [
            {"id": "REQ-001", "priority": "P0", "title": "Double-Entry Ledger", "acceptance_criteria": ["Debits must equal credits", "ACID compliant"]}
        ],
        "non_functional_slas": [
            {"metric": "P95 Latency", "target": "< 25ms", "verification_method": "k6 load test"},
            {"metric": "Throughput", "target": "10,000 tx/sec", "verification_method": "Distributed stress test"}
        ],
        "security_threat_matrix": [
            {"threat_category": "Tampering", "threat_description": "Transaction replay attacks", "mitigation": "HMAC-SHA256 signature verification"}
        ],
        "architecture": {
            "database_ddl": "CREATE TABLE ledger_entries (id UUID PRIMARY KEY, amount NUMERIC(18, 4));",
            "database_models": [],
            "api_contracts": []
        },
        "lifecycle": {
            "failure_recovery_matrix": [
                {"component": "PostgreSQL Replica", "detection_sla": "< 2s", "recovery_mechanism": "Patroni automated failover"}
            ]
        }
    }


class TestVoGenFlowDesktop:
    """Comprehensive test suite for VoGenFlow Modernized Desktop Application."""

    def test_window_initialization(self, qapp):
        """Verify window initializes with correct title, dimensions, and 4 navigation views."""
        win = MainWindow(default_theme="onyx", default_backend="auto")
        assert "VoGenFlow" in win.windowTitle()
        assert win.main_nav_tabs.count() == 4
        assert "Voice" in win.main_nav_tabs.tabText(0)
        assert "Council" in win.main_nav_tabs.tabText(1)
        assert "Specification" in win.main_nav_tabs.tabText(2)
        assert "ProjectIR" in win.main_nav_tabs.tabText(3)
        assert win.current_theme == "onyx"

    def test_monolith_theme_switching(self, qapp):
        """Verify dynamic theme switching between Onyx True Black and Vellum Luxury Light."""
        win = MainWindow(default_theme="onyx")
        assert win.current_theme == "onyx"
        assert win.visualizer.theme == "onyx"

        # Switch to Vellum Light
        win.set_theme("vellum")
        assert win.current_theme == "vellum"
        assert win.visualizer.theme == "vellum"
        assert "Vellum" in win.status_label.text()
        for highlighter in win.highlighters.values():
            assert highlighter.theme == "vellum"

        # Switch back to Onyx Black
        win.set_theme("onyx")
        assert win.current_theme == "onyx"
        assert win.visualizer.theme == "onyx"
        assert "Onyx" in win.status_label.text()
        for highlighter in win.highlighters.values():
            assert highlighter.theme == "onyx"

    def test_council_chamber_6_agents(self, qapp):
        """Verify Council Deliberation Chamber viewer registers and updates all 6 agents."""
        win = MainWindow()
        expected_agents = [
            ("pm_agent", "Product Manager", "SEAT 1"),
            ("architect_agent", "System Architect", "SEAT 2"),
            ("ui_agent", "UI/UX Engineer", "SEAT 3"),
            ("systems_agent", "Lifecycle Engineer", "SEAT 4"),
            ("agile_agent", "Agile Delivery Lead", "SEAT 5"),
            ("diff_agent", "Delta Refiner", "SEAT 6"),
        ]

        for role_key, title_sub, seat_sub in expected_agents:
            assert role_key in win.agent_cards, f"Agent {role_key} missing from agent_cards"
            card = win.agent_cards[role_key]
            assert title_sub in card.name_label.text()
            assert seat_sub in card.seat_label.text()

            # Test status update
            card.set_status("DELIBERATING", "Synthesizing specs...")
            assert "DELIBERATING" in card.status_pill.text()

            card.set_status("COMPLETED", tokens=420, latency=1.15, thoughts="Deliberation finished successfully.")
            assert "COMPLETED" in card.status_pill.text()
            assert "420 tokens" in card.telemetry_label.text()
            assert "Deliberation finished" in card.thoughts_edit.toPlainText()

    def test_specification_studio_load_and_preview(self, qapp, sample_artifacts):
        """Verify Specification Studio loads all specifications and supports markdown preview."""
        win = MainWindow()
        win.load_mock_artifacts(sample_artifacts)

        # Check raw editors contain expected content
        assert "Global Payments Gateway PRD" in win.spec_editors["PRD.md"].toPlainText()
        assert "CREATE TABLE accounts" in win.spec_editors["Architecture.md"].toPlainText()
        assert "sequenceDiagram" in win.spec_editors["Flow.md"].toPlainText()
        assert "Milestone 1" in win.spec_editors["tasks.md"].toPlainText()
        assert "Palette Tokens" in win.spec_editors["design.md"].toPlainText()

        # Check toggle to rendered preview mode
        prd_stack = win.spec_stacks["PRD.md"]
        prd_raw = win.spec_editors["PRD.md"]
        prd_preview = win.spec_previews["PRD.md"]

        assert prd_stack.currentIndex() == 0  # starts in raw editor
        win._toggle_preview_mode(prd_stack, prd_raw, prd_preview)
        assert prd_stack.currentIndex() == 1  # toggled to preview
        assert len(prd_preview.toPlainText()) > 0

        # Toggle back to raw editor
        win._toggle_preview_mode(prd_stack, prd_raw, prd_preview)
        assert prd_stack.currentIndex() == 0

    def test_project_ir_ast_inspection(self, qapp, sample_artifacts, sample_project_ir):
        """Verify ProjectIR inspector parses metadata, PostgreSQL DDL, and SLA/Threat tables."""
        win = MainWindow()
        win.load_mock_artifacts(sample_artifacts, project_ir=sample_project_ir)

        # Overview View
        assert "Global Payments & Settlement Gateway" in win.ir_overview_edit.toPlainText()
        assert "High-velocity multi-currency" in win.ir_overview_edit.toPlainText()

        # DDL View
        assert "CREATE TABLE ledger_entries" in win.ir_ddl_edit.toPlainText()

        # Table rendering for SLAs
        win._render_ir_table_view("⏱️ Non-Functional SLAs")
        assert win.ir_table_widget.rowCount() == 2
        assert win.ir_table_widget.columnCount() == 3
        assert win.ir_table_widget.item(0, 0).text() == "P95 Latency"
        assert win.ir_table_widget.item(0, 1).text() == "< 25ms"

        # Table rendering for STRIDE Threat Matrix
        win._render_ir_table_view("🛡️ STRIDE Threat Matrix")
        assert win.ir_table_widget.rowCount() == 1
        assert win.ir_table_widget.item(0, 0).text() == "Tampering"
        assert "replay" in win.ir_table_widget.item(0, 1).text()

    def test_client_side_word_docx_export(self, qapp, sample_artifacts, sample_project_ir):
        """Verify 1-Click Client-Side Word (.docx) export bundles all 5 specs via python-docx."""
        win = MainWindow()
        win.load_mock_artifacts(sample_artifacts, project_ir=sample_project_ir)

        with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as tf:
            temp_path = tf.name

        try:
            saved_path = win.export_to_docx(target_path=temp_path)
            assert saved_path == temp_path
            assert os.path.exists(saved_path)
            file_size = os.path.getsize(saved_path)
            assert file_size > 5000, f"Exported file is too small: {file_size} bytes"

            # Inspect Word document structure via python-docx
            doc = docx.Document(saved_path)
            full_text = "\n".join([p.text for p in doc.paragraphs])

            # Check cover and title
            assert "VOGENFLOW INDUSTRIAL SPECIFICATION" in full_text
            assert "Global Payments & Settlement Gateway" in full_text

            # Check all 5 core specification headings are present
            assert "1. Product Requirements Document (PRD)" in full_text
            assert "2. System Architecture & PostgreSQL DDL" in full_text
            assert "3. Lifecycle Sequence Flows & Operational Recovery" in full_text
            assert "4. Phased Engineering Tasks & Verification Plan" in full_text
            assert "5. Monolith Luxury UI/UX Design System" in full_text

            # Check table generation in Word document
            assert len(doc.tables) >= 2
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def test_audio_visualizer_decay_and_reset(self, qapp):
        """Verify AudioVisualizer handles level setting, theme, and decay."""
        viz = AudioVisualizer(num_bars=16)
        viz.set_theme("vellum")
        assert viz.theme == "vellum"
        viz.set_level(0.85)
        assert viz.is_active is True
        assert viz.target_level == 0.85

        viz._update_decay()
        assert sum(viz.levels) > 0.0

        viz.reset()
        assert viz.is_active is False
        assert viz.target_level == 0.0
        assert sum(viz.levels) == 0.0

    def test_drop_zone_widget(self, qapp):
        """Verify DropZoneWidget initialization."""
        drop = DropZoneWidget()
        assert drop.acceptDrops() is True
        assert "Drag & Drop Audio File" in drop.label.text()

    def test_standalone_headless_launcher(self):
        """Verify run_desktop.py dry-run executes cleanly in headless mode."""
        exit_code = run_headless_dry_run(theme="onyx", test_docx=True)
        assert exit_code == 0

    def test_standalone_cli_execution(self):
        """Verify calling run_desktop.py via subprocess with --dry-run exits with 0."""
        cmd = [sys.executable, str(PROJECT_ROOT / "run_desktop.py"), "--dry-run"]
        res = subprocess.run(cmd, capture_output=True, text=True, cwd=str(PROJECT_ROOT), timeout=25)
        assert res.returncode == 0, f"run_desktop.py failed:\nSTDOUT: {res.stdout}\nSTDERR: {res.stderr}"
        assert "VoGenFlow Desktop Headless Dry-Run PASSED" in res.stdout or "VoGenFlow Desktop Headless Dry-Run PASSED" in res.stderr
