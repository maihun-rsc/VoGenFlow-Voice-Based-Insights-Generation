"""Unit tests for ModelRouter and CircuitBreaker."""

import unittest
import time
from src.model_router import ModelRouter, CircuitBreaker, ROLE_MODEL_MAPPING


class TestModelRouter(unittest.TestCase):
    def setUp(self):
        # Initialize router with min interval = 0.05 for fast test execution
        self.router = ModelRouter(api_key=None, min_request_interval=0.05)

    def test_role_model_mappings(self):
        self.assertEqual(self.router.get_model_for_role("pm_agent"), "openai/gpt-oss-120b")
        self.assertEqual(self.router.get_model_for_role("architect_agent"), "qwen/qwen3.6-27b")
        self.assertEqual(self.router.get_model_for_role("ui_agent"), "qwen/qwen3.6-27b")
        self.assertEqual(self.router.get_model_for_role("systems_agent"), "openai/gpt-oss-120b")
        self.assertEqual(self.router.get_model_for_role("diff_agent"), "openai/gpt-oss-20b")
        self.assertEqual(self.router.get_model_for_role("unknown_role"), "openai/gpt-oss-20b")

    def test_circuit_breaker_logic(self):
        cb = CircuitBreaker(failure_threshold=2, recovery_time=0.1)
        self.assertTrue(cb.allow_request())
        self.assertEqual(cb.state, "CLOSED")

        cb.record_failure()
        self.assertEqual(cb.state, "CLOSED")

        cb.record_failure()
        self.assertEqual(cb.state, "OPEN")
        self.assertFalse(cb.allow_request())

        # Wait for recovery
        time.sleep(0.15)
        self.assertTrue(cb.allow_request())
        self.assertEqual(cb.state, "HALF_OPEN")

        cb.record_success()
        self.assertEqual(cb.state, "CLOSED")

    def test_fallback_generation(self):
        result = self.router.generate(
            role="pm_agent",
            system_prompt="You are a PM.",
            user_prompt="Build a SaaS platform for real-time video transcription."
        )
        self.assertEqual(result["role"], "pm_agent")
        self.assertIn("PRD", result["content"])
        self.assertEqual(result["status"], "fallback_success")
        self.assertGreater(result["prompt_tokens"], 0)

    def test_telemetry_tracking(self):
        initial_calls = self.router.telemetry["total_calls"]
        self.router.generate(role="architect_agent", system_prompt="Sys", user_prompt="Test Arch")
        self.assertEqual(self.router.telemetry["total_calls"], initial_calls + 1)
        self.assertIn("architect_agent", self.router.telemetry["calls_per_role"])

    def test_rate_pacing(self):
        t0 = time.time()
        self.router.generate(role="ui_agent", system_prompt="UI", user_prompt="Prompt 1")
        self.router.generate(role="ui_agent", system_prompt="UI", user_prompt="Prompt 2")
        elapsed = time.time() - t0
        self.assertGreaterEqual(elapsed, 0.05)


if __name__ == "__main__":
    unittest.main()
