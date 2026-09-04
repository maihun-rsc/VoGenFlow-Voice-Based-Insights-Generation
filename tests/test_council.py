"""Unit tests for CouncilEngine."""

import unittest
import tempfile
import os
import shutil
from src.council_engine import CouncilEngine, COUNCIL_PRESETS
from src.model_router import ModelRouter
from src.knowledge_db import CuratedKnowledgeDB


class TestCouncilEngine(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.router = ModelRouter(api_key=None, min_request_interval=0.01)
        self.knowledge_db = CuratedKnowledgeDB()
        self.engine = CouncilEngine(model_router=self.router, knowledge_db=self.knowledge_db)

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_deliberate_standard_preset(self):
        progress_events = []

        def on_progress(role, data):
            progress_events.append((role, data.get("message")))

        transcript = "We need an end-to-end voice AI platform that writes C4 architecture and triggers automated PRs."
        result = self.engine.deliberate(transcript, preset="standard", progress_callback=on_progress)

        self.assertEqual(result["status"], "completed")
        self.assertIn("PRD.md", result["artifacts"])
        self.assertIn("Architecture.md", result["artifacts"])
        self.assertIn("design_proposal.md", result["artifacts"])
        self.assertIn("Flow.md", result["artifacts"])
        self.assertIn("tasks.md", result["artifacts"])
        self.assertIn("master_execution_bundle.md", result["artifacts"])
        self.assertGreater(len(progress_events), 0)

    def test_deliberate_security_pentest_preset(self):
        transcript = "Perform security audit on our API endpoints."
        result = self.engine.deliberate(transcript, preset="security_pentest")

        self.assertEqual(result["status"], "completed")
        self.assertIn("PRD.md", result["artifacts"])
        self.assertIn("Architecture.md", result["artifacts"])
        self.assertIn("Flow.md", result["artifacts"])
        self.assertNotIn("ui_agent", [t.get("role") for t in result["telemetry"]])

    def test_persist_artifacts(self):
        artifacts = {
            "test_spec.md": "# Test Spec Content",
            "test_c4.md": "flowchart TD\nA-->B"
        }
        saved = self.engine.persist_artifacts("test_session_101", artifacts, target_dir=self.temp_dir)
        self.assertEqual(len(saved), 2)
        for filepath in saved:
            self.assertTrue(os.path.exists(filepath))

    def test_deliberate_lean_sprint_preset(self):
        transcript = "Build a lightweight MVP microservice for real-time notifications."
        result = self.engine.deliberate(transcript, preset="lean_sprint")
        self.assertEqual(result["status"], "completed")
        self.assertIn("PRD.md", result["artifacts"])
        self.assertIn("Architecture.md", result["artifacts"])
        self.assertIn("tasks.md", result["artifacts"])
        self.assertIn("master_execution_bundle.md", result["artifacts"])
        self.assertNotIn("ui_agent", [t.get("role") for t in result["telemetry"]])
        self.assertNotIn("systems_agent", [t.get("role") for t in result["telemetry"]])
        self.assertNotIn("design_proposal.md", result["artifacts"])
        self.assertNotIn("Flow.md", result["artifacts"])

    def test_deliberate_unknown_preset_fallback(self):
        transcript = "Build an enterprise portal."
        result = self.engine.deliberate(transcript, preset="non_existent_preset_xyz")
        self.assertEqual(result["status"], "completed")
        self.assertEqual(len(result["artifacts"]), 6)
        self.assertIn("design_proposal.md", result["artifacts"])

    def test_persist_artifacts_default_output_dir(self):
        from src.config import Config
        session_id = "test_verify_session_404"
        artifacts = {"PRD.md": "# Test PRD", "Architecture.md": "# Test Arch"}
        saved = self.engine.persist_artifacts(session_id, artifacts)
        expected_dir = Config.OUTPUT_DIR / "sessions" / session_id
        self.assertTrue(expected_dir.exists(), f"Expected directory {expected_dir} does not exist!")
        self.assertEqual(len(saved), 2)
        for p in saved:
            self.assertTrue(os.path.exists(p))
        # Cleanup
        shutil.rmtree(expected_dir, ignore_errors=True)

    def test_council_presets_metadata(self):
        self.assertIn("standard", COUNCIL_PRESETS)
        self.assertIn("security_pentest", COUNCIL_PRESETS)
        self.assertIn("lean_sprint", COUNCIL_PRESETS)
        self.assertEqual(len(COUNCIL_PRESETS["standard"]["roles"]), 6)
        self.assertEqual(COUNCIL_PRESETS["standard"]["name"], "Standard Monolith Council (6-Seat)")
        self.assertEqual(len(COUNCIL_PRESETS["security_pentest"]["roles"]), 4)
        self.assertEqual(len(COUNCIL_PRESETS["lean_sprint"]["roles"]), 4)


if __name__ == "__main__":
    unittest.main()
