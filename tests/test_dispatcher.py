"""Unit tests for MasterPromptCompiler and PRDispatcher."""

import unittest
import os
import tempfile
import subprocess
from src.master_prompt_compiler import MasterPromptCompiler
from src.pr_dispatcher import PRDispatcher


class TestDispatcherAndCompiler(unittest.TestCase):
    def setUp(self):
        self.compiler = MasterPromptCompiler()
        self.dispatcher = PRDispatcher()

    def test_compiler_output(self):
        artifacts = {
            "PRD.md": "# PRD\n- P0: Audio pipeline",
            "Architecture.md": "# Architecture\n```mermaid\nflowchart TD\nA-->B\n```",
            "design_proposal.md": "# UI\n- Linear Dark Tokens",
            "Flow.md": "# Flow\n```mermaid\nsequenceDiagram\nU->>S: Audio\n```",
            "tasks.md": "# Tasks\n- [ ] Deploy"
        }
        bundle = self.compiler.compile("test_session_99", artifacts)
        self.assertIn("MASTER EXECUTION BUNDLE", bundle)
        self.assertIn("P0: Audio pipeline", bundle)
        self.assertIn("Linear Dark Tokens", bundle)

        validation = self.compiler.validate_bundle(bundle)
        self.assertTrue(validation["valid"], f"Validation failed with errors: {validation['errors']}")
        self.assertEqual(len(validation["errors"]), 0)

    def test_compiler_validation_error(self):
        bad_bundle = "# Incomplete Bundle\n```python\nprint('unclosed fence')"
        validation = self.compiler.validate_bundle(bad_bundle)
        self.assertFalse(validation["valid"])
        self.assertGreater(len(validation["errors"]), 0)

    def test_dispatcher_branch_and_rollback(self):
        current = self.dispatcher.get_current_branch()
        self.assertTrue(bool(current))

        test_branch = "test-tmp-branch-vogenflow"
        # Create branch
        res = self.dispatcher.create_feature_branch(test_branch)
        self.assertEqual(res["status"], "success")
        self.assertEqual(self.dispatcher.get_current_branch(), test_branch)

        # Rollback back to main
        success = self.dispatcher.rollback(test_branch, fallback_branch=current)
        self.assertTrue(success)
        self.assertEqual(self.dispatcher.get_current_branch(), current)

    def test_dispatch_pr_payload(self):
        res = self.dispatcher.dispatch_pr(
            title="feat: Vo-Gen-Flow 2.0 autonomous update",
            body="Autonomous pull request dispatched by Vo-Gen-Flow Council.",
            base_branch="main"
        )
        self.assertIn(res["status"], ["prepared", "dispatched"])
        self.assertEqual(res["title"], "feat: Vo-Gen-Flow 2.0 autonomous update")


if __name__ == "__main__":
    unittest.main()
