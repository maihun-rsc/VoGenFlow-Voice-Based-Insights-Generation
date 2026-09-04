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


if __name__ == "__main__":
    unittest.main()
