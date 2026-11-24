"""
tests/test_desktop_gui_simulation.py
Automated GUI Simulation Test Suite for VoGenFlow PyQt6 Desktop Application.

Uses pytest-qt and QtBot under headless offscreen mode (QT_QPA_PLATFORM=offscreen).
Verifies all 6 core feature flows:
1. Voice Dictation & Audio Visualizer (Sample ingress, amplitude decay, reset, drop zone, headless record)
2. 6-Agent Council Chamber (Agent cards, deliberation progress, status transitions, open studio)
3. Multi-Tab Specification Studio (PRD, Architecture, Flow, Tasks, Design, Bundle tabs; raw vs preview toggle)
4. ProjectIR Schema Inspector (Tree navigation: Overview, DDL, SLAs, STRIDE, Requirements, Personas, JSON)
5. Word .docx Export (Direct target_path export and GUI button export via monkeypatched file dialog)
6. Monolith Theme Switching and Clean Window Close via closeEvent
"""

import os
import sys
import docx
from pathlib import Path
from typing import Dict, Any

import pytest
from PyQt6.QtCore import Qt, QMimeData, QUrl, QPoint
from PyQt6.QtGui import QDropEvent
from PyQt6.QtWidgets import QMessageBox, QFileDialog, QPushButton, QTreeWidgetItem

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Ensure headless offscreen platform for Qt
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from src.ui.main_window import MainWindow, DropZoneWidget, CouncilAgentCard
from src.ui.audio_visualizer import AudioVisualizer
from src.models.project_ir import ProjectIR, create_project_ir_from_council_artifacts


@pytest.fixture
def mock_gui_data() -> Dict[str, Any]:
    """Rich mock artifacts, ProjectIR, and seat dossiers for desktop simulation."""
    artifacts = {
        "PRD.md": (
            "# VoGenFlow Autonomous Voice Platform PRD\n\n"
            "## 1. Executive Summary & Problem Statement\n"
            "Transforms spoken developer streams into formal software architecture specifications.\n\n"
            "## 2. Target Personas\n"
            "- Principal Systems Architect\n"
            "- Staff Backend Engineer\n\n"
            "## 3. Non-Functional SLAs Table\n"
            "| Metric | Target | Verification Method |\n"
            "|---|---|---|\n"
            "| P95 Ingress Latency | < 30ms | Load testing |\n"
            "| Availability | 99.99% | Pingdom probe |\n\n"
            "## 4. STRIDE Security Threat Matrix\n"
            "| Category | Threat Description | Mitigation |\n"
            "|---|---|---|\n"
            "| Spoofing | Unauthorized client access | Ed25519 JWT verification |\n"
            "| Tampering | Parameter injection | Parameterized SQL queries |\n"
        ),
        "Architecture.md": (
            "# System Architecture & PostgreSQL DDL\n\n"
            "```mermaid\n"
            "flowchart TD\n"
            "    User[User Audio] --> Gateway[FastAPI Ingress 8080]\n"
            "    Gateway --> DB[(PostgreSQL 16 + RLS)]\n"
            "```\n\n"
            "```sql\n"
            "CREATE EXTENSION IF NOT EXISTS \"pgcrypto\";\n\n"
            "CREATE TABLE sessions (\n"
            "    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),\n"
            "    tenant_id VARCHAR(64) NOT NULL,\n"
            "    transcript TEXT NOT NULL,\n"
            "    created_at TIMESTAMPTZ DEFAULT NOW()\n"
            ");\n\n"
            "ALTER TABLE sessions ENABLE ROW LEVEL SECURITY;\n"
            "CREATE POLICY sessions_tenant_isolation ON sessions\n"
            "    FOR ALL\n"
            "    USING (tenant_id = current_setting('app.current_tenant', true));\n"
            "```\n"
        ),
        "Flow.md": (
            "# Systems Lifecycle & Transaction Flow\n\n"
            "```mermaid\n"
            "sequenceDiagram\n"
            "    autonumber\n"
            "    User->>DesktopApp: Dictate Audio Brainstorm\n"
            "    DesktopApp->>CouncilEngine: Convene 6-Seat Council\n"
            "    CouncilEngine-->>DesktopApp: Stream Artifacts Bundle\n"
            "```\n"
        ),
        "tasks.md": (
            "# Phased Engineering Delivery Milestones\n\n"
            "## Milestone 1: Core Persistence\n"
            "- [x] SQLite WAL database schemas\n"
            "- [ ] Redis cluster configuration\n\n"
            "## Milestone 2: Desktop GUI & Testing\n"
            "- [x] PyQt6 MainWindow implementation\n"
            "- [x] pytest-qt simulation suite\n"
        ),
        "design.md": (
            "# Monolith Luxury Design Specification\n\n"
            "## Palette Tokens\n"
            "- Onyx Black: `#000000`\n"
            "- Vellum Light: `#F7F6F2`\n"
            "- Brushed Gold: `#D4AF37`\n"
        ),
        "master_execution_bundle.md": (
            "# Master Execution Bundle: VoGenFlow\n\n"
            "Unified blueprint consolidating PRD, Architecture, Flow, Tasks, and Design.\n"
        ),
    }

    project_ir = {
        "project_name": "VoGenFlow Enterprise",
        "tagline": "Spoken Audio to Industrial-Grade SaaS Specifications",
        "executive_summary": "Autonomous voice-to-architecture platform generating multi-tenant systems.",
        "target_personas": [
            {
                "name": "Principal Systems Architect",
                "role": "Designs distributed backends and database schemas",
                "pain_points": ["Manual specification drift", "Slow sprint kickoff"],
                "needs": ["Automated PostgreSQL DDL", "C4 diagrams", "Phased tasks"],
            },
            {
                "name": "Agile Delivery Lead",
                "role": "Manages cross-functional sprint deliveries",
                "pain_points": ["Ambiguous requirements", "Missing verification commands"],
                "needs": ["Structured checklist", "Acceptance criteria"],
            },
        ],
        "requirements": [
            {
                "id": "REQ-001",
                "priority": "P0",
                "title": "Real-time Voice Ingress & Transcription",
                "user_story": "As an engineer, I want to dictate my thoughts and have them transcribed immediately.",
                "acceptance_criteria": ["Whisper large-v3-turbo integration", "P95 transcription < 1.5s"],
            },
            {
                "id": "REQ-002",
                "priority": "P0",
                "title": "Deterministic 6-Agent Deliberation",
                "user_story": "As an architect, I want 6 specialized AI seats deliberating concurrently.",
                "acceptance_criteria": ["Fan-Out execution", "Canonical blackboard sharing"],
            },
        ],
        "non_functional_slas": [
            {"metric": "P95 Ingress Latency", "target": "< 30ms", "verification_method": "k6 load simulation"},
            {"metric": "System Availability", "target": "99.99%", "verification_method": "Automated synthetic ping"},
            {"metric": "Max Concurrent Sessions", "target": "1000", "verification_method": "Distributed stress test"},
        ],
        "security_threat_matrix": [
            {"threat_category": "Spoofing", "threat_description": "Forged JWT tokens", "mitigation": "Ed25519 signature validation"},
            {"threat_category": "Tampering", "threat_description": "SQL injection in query parameters", "mitigation": "Parameterized queries & RLS"},
            {"threat_category": "Information Disclosure", "threat_description": "Cross-tenant data leakage", "mitigation": "PostgreSQL Row-Level Security policies"},
        ],
        "architecture": {
            "c4_mermaid_diagram": "flowchart TD\n  Client --> Gateway\n  Gateway --> DB",
            "database_ddl": "CREATE TABLE sessions (id UUID PRIMARY KEY, tenant_id VARCHAR(64));",
            "api_contracts": [],
            "models": [],
        },
        "lifecycle": {
            "sequence_diagram_mermaid": "sequenceDiagram\n  Client->>Server: Request\n  Server-->>Client: 200",
            "failure_recovery_matrix": [
                {"component": "Ingress Gateway", "detection_sla": "< 500ms", "recovery_mechanism": "Automated pod restart"},
                {"component": "Database Connection Pool", "detection_sla": "< 1000ms", "recovery_mechanism": "Failover to hot standby"},
            ],
        },
        "tasks": [
            {
                "milestone_id": "M1",
                "title": "Persistence Core",
                "tasks": [{"description": "Create SQLite schema", "file_target": "src/db/sqlite_store.py", "verification_command": "pytest tests/test_sqlite_store.py"}],
            }
        ],
    }

    seat_dossier = {
        "pm_agent": {
            "name": "Strategist",
            "role": "Principal Technical PM",
            "model": "openai/gpt-oss-120b",
            "latency_seconds": 0.42,
            "tokens": 480,
            "thoughts": "Synthesized executive summary, target personas, P0 requirements, and SLAs.",
            "stage": "STAGE 1 // CANONICAL CORE",
            "artifact_key": "PRD.md",
        },
        "architect_agent": {
            "name": "Architect",
            "role": "Lead Systems Architect",
            "model": "openai/gpt-oss-120b",
            "latency_seconds": 0.51,
            "tokens": 530,
            "thoughts": "Designed high-velocity microservice topology and PostgreSQL DDL with RLS.",
            "stage": "STAGE 2 // PARALLEL FAN-OUT",
            "artifact_key": "Architecture.md",
        },
        "ui_agent": {
            "name": "Staff UI/UX",
            "role": "Staff UI/UX Engineer",
            "model": "meta-llama/llama-3.3-70b-versatile",
            "latency_seconds": 0.38,
            "tokens": 410,
            "thoughts": "Specified Monolith Luxury Onyx and Vellum design tokens and component trees.",
            "stage": "STAGE 2 // PARALLEL FAN-OUT",
            "artifact_key": "design.md",
        },
        "systems_agent": {
            "name": "Systems Lifecycle",
            "role": "Systems Lifecycle Engineer",
            "model": "openai/gpt-oss-120b",
            "latency_seconds": 0.44,
            "tokens": 460,
            "thoughts": "Modeled transaction sequence diagrams and operational recovery matrix.",
            "stage": "STAGE 2 // PARALLEL FAN-OUT",
            "artifact_key": "Flow.md",
        },
        "agile_agent": {
            "name": "Agile Delivery",
            "role": "Agile Delivery Lead",
            "model": "meta-llama/llama-3.3-70b-versatile",
            "latency_seconds": 0.35,
            "tokens": 390,
            "thoughts": "Structured 4 engineering milestones with explicit verification commands.",
            "stage": "STAGE 2 // PARALLEL FAN-OUT",
            "artifact_key": "tasks.md",
        },
        "diff_agent": {
            "name": "Delta Refiner",
            "role": "Master Packager",
            "model": "openai/gpt-oss-120b",
            "latency_seconds": 0.60,
            "tokens": 620,
            "thoughts": "Gathered all 5 domain specifications into unified master execution bundle.",
            "stage": "STAGE 3 // GATHER & REFINE",
            "artifact_key": "master_execution_bundle.md",
        },
    }

    return {
        "artifacts": artifacts,
        "project_ir": project_ir,
        "seat_dossier": seat_dossier,
    }


@pytest.fixture
def app_window(qtbot, mock_gui_data):
    """Instantiate MainWindow under qtbot and pre-load mock data."""
    win = MainWindow(default_theme="onyx", default_backend="in_process")
    qtbot.addWidget(win)
    win.show()
    win.load_mock_artifacts(
        artifacts=mock_gui_data["artifacts"],
        project_ir=mock_gui_data["project_ir"],
        seat_dossier=mock_gui_data["seat_dossier"],
    )
    yield win
    win.close()


class TestDesktopGUISimulation:
    """Comprehensive automated GUI simulation test suite exercising all 6 core features."""

    # =========================================================================
    # 1. VOICE DICTATION & AUDIO VISUALIZER
    # =========================================================================
    def test_voice_dictation_and_audio_visualizer(self, app_window, qtbot):
        """Simulate sample audio memo loading, amplitude ingress, decay animation, and drop zone."""
        win = app_window
        win.main_nav_tabs.setCurrentIndex(0)

        # 1.1 Click 'Load Sample Memo' button
        qtbot.mouseClick(win.sample_btn, Qt.MouseButton.LeftButton)
        assert len(win.transcript_edit.toPlainText().strip()) > 20
        assert "microservice" in win.transcript_edit.toPlainText() or "platform" in win.transcript_edit.toPlainText()

        # 1.2 Verify transcript telemetry statistics update
        stats_text = win.transcript_stats_label.text()
        assert "Words:" in stats_text
        assert "Duration:" in stats_text

        # 1.3 Audio Visualizer Amplitude Ingress
        win._on_audio_amplitude(0.95)
        assert win.visualizer.is_active
        assert win.visualizer.target_level >= 0.90
        # Wait for animation decay step
        qtbot.wait(60)
        assert any(lvl > 0.0 for lvl in win.visualizer.levels)

        # 1.4 Visualizer Decay and Reset
        win.visualizer.reset()
        assert not win.visualizer.is_active
        assert all(lvl == 0.0 for lvl in win.visualizer.levels)

        # 1.5 DropZoneWidget simulation
        mime = QMimeData()
        mime.setUrls([QUrl.fromLocalFile("data/sample_audio.wav")])
        drop_event = QDropEvent(
            QPoint(10, 10).toPointF(),
            Qt.DropAction.CopyAction,
            mime,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
        )
        win.drop_zone.dropEvent(drop_event)
        assert "Loaded" in win.status_label.text() or "sample_audio.wav" in win.selected_file_label.text()

        # 1.6 Headless Record Toggle safety check (must not raise exception)
        win._toggle_recording()
        # In offscreen mode, recording is safely guarded
        assert "unavailable" in win.status_label.text().lower() or "recording" in win.status_label.text().lower()
        if win.recorder.is_recording:
            win._toggle_recording()

    # =========================================================================
    # 2. 6-AGENT COUNCIL CHAMBER DELIBERATION
    # =========================================================================
    def test_six_agent_council_chamber_simulation(self, app_window, qtbot, mock_gui_data):
        """Verify all 6 seats, progress signals, thought dossiers, and studio transition."""
        win = app_window
        win.main_nav_tabs.setCurrentIndex(1)

        # 2.1 Verify all 6 agent seats are registered
        expected_seats = [
            "pm_agent",
            "architect_agent",
            "ui_agent",
            "systems_agent",
            "agile_agent",
            "diff_agent",
        ]
        for seat in expected_seats:
            assert seat in win.agent_cards, f"Seat {seat} missing from council chamber"
            card = win.agent_cards[seat]
            assert isinstance(card, CouncilAgentCard)
            assert len(card.role_label.text()) > 0

        # 2.2 Simulate deliberation progress signal
        win._on_council_progress("Synthesizing PRD & Canonical Core...", {"role": "pm_agent"})
        pm_card = win.agent_cards["pm_agent"]
        assert "DELIBERATING" in pm_card.status_pill.text()
        assert "Synthesizing PRD" in win.chamber_log_edit.toPlainText()

        # 2.3 Simulate deliberation completion signal
        mock_result = {
            "artifacts": mock_gui_data["artifacts"],
            "project_ir": mock_gui_data["project_ir"],
            "seat_dossier": mock_gui_data["seat_dossier"],
        }
        win._on_council_finished(mock_result)

        # Verify progress bar reaches 100% and chamber status reflects consensus
        assert win.chamber_progress_bar.value() == 100
        assert "COMPLETE" in win.chamber_status_label.text()

        # 2.4 Verify all 6 cards reflect COMPLETED state and seat dossiers
        for seat in expected_seats:
            card = win.agent_cards[seat]
            assert "COMPLETED" in card.status_pill.text()
            assert len(card.thoughts_edit.toPlainText()) > 10
            assert "tokens" in card.telemetry_label.text().lower()

        # 2.5 Click 'OPEN SPECIFICATION STUDIO' button
        qtbot.mouseClick(win.open_studio_btn, Qt.MouseButton.LeftButton)
        assert win.main_nav_tabs.currentIndex() == 2  # Specification Studio

    # =========================================================================
    # 3. MULTI-TAB SPECIFICATION STUDIO
    # =========================================================================
    def test_multi_tab_specification_studio_and_preview_toggle(self, app_window, qtbot):
        """Verify all 6 specification tabs and toggle between Raw Editor and Rendered Markdown Preview."""
        win = app_window
        win.main_nav_tabs.setCurrentIndex(2)

        # Check all 6 specification tabs
        actual_tab_count = win.spec_tabs.count()
        assert actual_tab_count == 6

        spec_file_keys = [
            "PRD.md",
            "Architecture.md",
            "Flow.md",
            "tasks.md",
            "design.md",
            "master_execution_bundle.md",
        ]

        for idx, file_key in enumerate(spec_file_keys):
            win.spec_tabs.setCurrentIndex(idx)
            tab_widget = win.spec_tabs.widget(idx)

            raw_editor = win.spec_editors.get(file_key)
            preview_editor = win.spec_previews.get(file_key)
            stack = win.spec_stacks.get(file_key)

            assert raw_editor is not None
            assert preview_editor is not None
            assert stack is not None

            # Verify raw editor has non-empty loaded content
            raw_content = raw_editor.toPlainText().strip()
            assert len(raw_content) > 20, f"Specification tab {file_key} raw content is empty"

            # 3.1 Initial state: Page 0 (Raw Markdown Editor)
            assert stack.currentIndex() == 0

            # Find the 'Toggle Markdown Preview' button in this tab
            toggle_btns = [b for b in tab_widget.findChildren(QPushButton) if "Toggle" in b.text()]
            assert len(toggle_btns) == 1
            toggle_btn = toggle_btns[0]

            # 3.2 Click 'Toggle Markdown Preview' -> transition to Page 1
            qtbot.mouseClick(toggle_btn, Qt.MouseButton.LeftButton)
            assert stack.currentIndex() == 1
            # Verify rendered preview editor has content
            assert len(preview_editor.toPlainText().strip()) > 0

            # 3.3 Click 'Toggle Markdown Preview' again -> transition back to Page 0
            qtbot.mouseClick(toggle_btn, Qt.MouseButton.LeftButton)
            assert stack.currentIndex() == 0

    # =========================================================================
    # 4. PROJECTIR SCHEMA INSPECTOR
    # =========================================================================
    def test_project_ir_schema_inspector_tree_navigation(self, app_window, qtbot):
        """Verify tree navigation across DDL, SLAs, STRIDE, Requirements, Personas, and Raw JSON."""
        win = app_window
        win.main_nav_tabs.setCurrentIndex(3)

        tree = win.ir_tree
        stack = win.ir_stack
        table = win.ir_table_widget

        # Collect all tree items
        items_by_text = {}
        for i in range(tree.topLevelItemCount()):
            item = tree.topLevelItem(i)
            items_by_text[item.text(0)] = item

        # 4.1 Click 'PostgreSQL Database DDL' -> Stack Index 1
        ddl_key = next((k for k in items_by_text if "PostgreSQL" in k), None)
        assert ddl_key is not None
        win._on_ir_tree_item_clicked(items_by_text[ddl_key], 0)
        assert stack.currentIndex() == 1
        assert "CREATE TABLE" in win.ir_ddl_edit.toPlainText()

        # 4.2 Click 'Non-Functional SLAs' -> Stack Index 2, Table view with 3 columns
        slas_key = next((k for k in items_by_text if "SLAs" in k), None)
        assert slas_key is not None
        win._on_ir_tree_item_clicked(items_by_text[slas_key], 0)
        assert stack.currentIndex() == 2
        assert table.columnCount() == 3
        assert table.rowCount() == 3
        assert table.horizontalHeaderItem(0).text() == "Metric"
        assert table.horizontalHeaderItem(1).text() == "Target"
        assert table.horizontalHeaderItem(2).text() == "Verification Method"
        assert table.item(0, 0).text() == "P95 Ingress Latency"

        # 4.3 Click 'STRIDE Threat Matrix' -> Stack Index 2, Table view with 3 columns
        stride_key = next((k for k in items_by_text if "STRIDE" in k), None)
        assert stride_key is not None
        win._on_ir_tree_item_clicked(items_by_text[stride_key], 0)
        assert stack.currentIndex() == 2
        assert table.columnCount() == 3
        assert table.rowCount() == 3
        assert table.horizontalHeaderItem(0).text() == "Category"
        assert table.item(0, 0).text() == "Spoofing"

        # 4.4 Click 'Functional Requirements' -> Stack Index 2, Table view with 4 columns
        reqs_key = next((k for k in items_by_text if "Requirements" in k), None)
        assert reqs_key is not None
        win._on_ir_tree_item_clicked(items_by_text[reqs_key], 0)
        assert stack.currentIndex() == 2
        assert table.columnCount() == 4
        assert table.rowCount() == 2
        assert table.horizontalHeaderItem(0).text() == "ID"
        assert table.item(0, 0).text() == "REQ-001"

        # 4.5 Click 'Target Personas' -> Stack Index 2, Table view with 4 columns (Remediation test!)
        personas_key = next((k for k in items_by_text if "Personas" in k), None)
        assert personas_key is not None
        win._on_ir_tree_item_clicked(items_by_text[personas_key], 0)
        assert stack.currentIndex() == 2
        assert table.columnCount() == 4
        assert table.rowCount() == 2
        assert table.horizontalHeaderItem(0).text() == "Name"
        assert table.horizontalHeaderItem(1).text() == "Role"
        assert table.horizontalHeaderItem(2).text() == "Pain Points"
        assert table.horizontalHeaderItem(3).text() == "Needs"
        assert table.item(0, 0).text() == "Principal Systems Architect"
        assert "Manual specification drift" in table.item(0, 2).text()

        # 4.6 Click 'Raw ProjectIR JSON' -> Stack Index 3
        json_key = next((k for k in items_by_text if "Raw ProjectIR" in k), None)
        assert json_key is not None
        win._on_ir_tree_item_clicked(items_by_text[json_key], 0)
        assert stack.currentIndex() == 3
        assert "VoGenFlow Enterprise" in win.ir_json_edit.toPlainText()

        # 4.7 Click 'Project Overview' -> Stack Index 0
        overview_key = next((k for k in items_by_text if "Overview" in k), None)
        assert overview_key is not None
        win._on_ir_tree_item_clicked(items_by_text[overview_key], 0)
        assert stack.currentIndex() == 0
        assert "VoGenFlow Enterprise" in win.ir_overview_edit.toPlainText()

    # =========================================================================
    # 5. WORD (.DOCX) EXPORT
    # =========================================================================
    def test_word_docx_export_direct_and_gui_button(self, app_window, qtbot, tmp_path, monkeypatch):
        """Verify both direct target_path export and GUI export_docx_btn click with monkeypatched file dialog."""
        win = app_window

        # 5.1 Direct export_to_docx with explicit target_path
        target_docx = tmp_path / "vogenflow_test_direct.docx"
        win.export_to_docx(target_path=str(target_docx))

        assert target_docx.exists()
        assert target_docx.stat().st_size > 2000

        doc = docx.Document(str(target_docx))
        assert len(doc.paragraphs) > 10
        assert len(doc.tables) >= 2

        # 5.2 GUI button click export (monkeypatching QFileDialog and QMessageBox to avoid blocking popups)
        btn_docx = tmp_path / "vogenflow_test_btn.docx"
        monkeypatch.setattr(
            QFileDialog,
            "getSaveFileName",
            lambda *args, **kwargs: (str(btn_docx), "Word Document (*.docx)"),
        )
        info_shown = []
        monkeypatch.setattr(
            QMessageBox,
            "information",
            lambda parent, title, text: info_shown.append(text),
        )

        win.main_nav_tabs.setCurrentIndex(2)
        qtbot.mouseClick(win.export_docx_btn, Qt.MouseButton.LeftButton)

        assert btn_docx.exists()
        assert btn_docx.stat().st_size > 2000
        assert len(info_shown) == 1
        assert "successfully" in info_shown[0].lower() or ".docx" in info_shown[0].lower()

        btn_doc = docx.Document(str(btn_docx))
        assert len(btn_doc.paragraphs) > 10

    # =========================================================================
    # 6. MONOLITH THEME SWITCHING & SAFE WINDOW CLOSE
    # =========================================================================
    def test_monolith_theme_switching_and_safe_window_close(self, app_window, qtbot):
        """Verify dynamic Onyx <-> Vellum theme toggle and clean closeEvent timer stoppage."""
        win = app_window

        # Initial theme is onyx
        assert win.current_theme == "onyx"

        # 6.1 Click theme button to toggle to Vellum
        qtbot.mouseClick(win.theme_btn, Qt.MouseButton.LeftButton)
        assert win.current_theme == "vellum"
        assert "VELLUM" in win.theme_btn.text().upper() or "LIGHT" in win.theme_btn.text().upper() or "ON" in win.theme_btn.text().upper()

        # 6.2 Click theme button again to toggle back to Onyx
        qtbot.mouseClick(win.theme_btn, Qt.MouseButton.LeftButton)
        assert win.current_theme == "onyx"

        # 6.3 Verify closeEvent stops timers safely
        assert win.ping_timer.isActive()
        assert win.visualizer.decay_timer.isActive()

        win.close()

        assert not win.ping_timer.isActive()
        assert not win.visualizer.decay_timer.isActive()
        assert not win.record_timer.isActive()

    # =========================================================================
    # 7. REGRESSION: EMPTY / NULL PROJECTIR HANDLING
    # =========================================================================
    def test_project_ir_none_fields_and_empty_ir_regression(self, app_window):
        """Verify _render_ir_table_view and load_mock_artifacts handle empty IR and explicit None fields safely."""
        win = app_window

        # 7.1 Empty / None project_ir shows visible notice row
        for empty_ir in (None, {}):
            win.project_ir = empty_ir
            win._render_ir_table_view("Non-Functional SLAs")
            assert win.ir_table_widget.rowCount() == 1
            assert win.ir_table_widget.columnCount() == 1
            assert win.ir_table_widget.item(0, 0) is not None
            assert "not yet synthesized" in win.ir_table_widget.item(0, 0).text().lower()

        # 7.2 ProjectIR with explicit None fields does not crash load_mock_artifacts or _render_ir_table_view
        none_ir = {
            "project_name": None,
            "tagline": None,
            "executive_summary": None,
            "target_personas": None,
            "requirements": None,
            "non_functional_slas": None,
            "security_threat_matrix": None,
            "lifecycle": None,
            "architecture": None,
        }
        win.load_mock_artifacts({}, project_ir=none_ir)
        assert "VoGenFlow Project" in win.ir_overview_edit.toPlainText()
        assert win.ir_ddl_edit.toPlainText() == ""

        for cat in ["Personas", "Requirements", "SLAs", "STRIDE", "Recovery"]:
            win._render_ir_table_view(cat)
            assert win.ir_table_widget.rowCount() == 0

        # 7.3 ProjectIR lists/dicts containing None subfields render empty strings safely
        partial_none_ir = {
            "project_name": "NullSubfieldsApp",
            "target_personas": [{"name": None, "role": None, "pain_points": None, "needs": None}],
            "requirements": [{"id": None, "priority": None, "title": None, "acceptance_criteria": None}],
            "non_functional_slas": [{"metric": None, "target": None, "verification_method": None}],
            "security_threat_matrix": [{"threat_category": None, "threat_description": None, "mitigation": None}],
            "lifecycle": {"failure_recovery_matrix": [{"component": None, "detection_sla": None, "recovery_mechanism": None}]},
        }
        win.project_ir = partial_none_ir
        for cat in ["Personas", "Requirements", "SLAs", "STRIDE", "Recovery"]:
            win._render_ir_table_view(cat)
            assert win.ir_table_widget.rowCount() == 1
            for col in range(win.ir_table_widget.columnCount()):
                assert win.ir_table_widget.item(0, col).text() == ""

        # Lifecycle with failure_recovery_matrix=None
        win.project_ir = {"lifecycle": {"failure_recovery_matrix": None}}
        win._render_ir_table_view("Recovery")
        assert win.ir_table_widget.rowCount() == 0
