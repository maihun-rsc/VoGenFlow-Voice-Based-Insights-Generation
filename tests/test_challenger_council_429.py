"""
tests/test_challenger_council_429.py
Empirical Challenger 2: Council Deliberation & ModelRouter 429 Resilience Verification.

Tests:
1. ModelRouter single-call failover on 429:
   - gpt-oss-120b raises 429 -> fails over to gpt-oss-20b (status=success, source=groq_api)
   - gpt-oss-120b AND gpt-oss-20b raise 429 -> fails over to qwen3.8-27b (status=success, source=groq_api)
2. ModelRouter exponential backoff retry on 429:
   - When all models hit 429 on Attempt 0, verifies exponential sleep and subsequent retry
3. ModelRouter fallback to offline template ONLY upon total exhaustion of all models and retries
4. Full CouncilEngine deliberation under simulated Groq 429:
   - Simulates 429 on gpt-oss-120b across all council seats
   - Verifies all seats complete via gpt-oss-20b failover
   - Verifies PRD.md, Architecture.md, and master_execution_bundle.md are dynamically produced
"""

import time
from unittest.mock import MagicMock, patch
import pytest

from src.model_router import ModelRouter, CircuitBreaker
from src.council_engine import CouncilEngine


class MockGroqChoice:
    def __init__(self, content: str, reasoning: str = ""):
        self.message = MagicMock(content=content, reasoning=reasoning)


class MockGroqUsage:
    def __init__(self, prompt_tokens: int = 50, completion_tokens: int = 150):
        self.prompt_tokens = prompt_tokens
        self.completion_tokens = completion_tokens


class MockGroqResponse:
    def __init__(self, content: str, reasoning: str = ""):
        self.choices = [MockGroqChoice(content, reasoning)]
        self.usage = MockGroqUsage()


class TestModelRouter429Failover:
    """Empirical verification of ModelRouter failover on Groq 429 rate limit errors."""

    def test_failover_120b_to_20b(self):
        """Simulate 429 on gpt-oss-120b; verify graceful failover to gpt-oss-20b without static fallback."""
        router = ModelRouter()
        router.groq_api_key = "gsk_test_mock_valid_key_1234567890"

        # Mock Groq client
        mock_groq = MagicMock()

        def side_effect(model, messages, **kwargs):
            if model == "openai/gpt-oss-120b":
                raise Exception("Error code: 429 - Rate limit reached for model openai/gpt-oss-120b")
            elif model == "openai/gpt-oss-20b":
                return MockGroqResponse(content="# Dynamic Spec from 20B Failover Engine\nLive tokens generated.")
            raise Exception(f"Unexpected model call: {model}")

        mock_groq.chat.completions.create.side_effect = side_effect
        router.groq_client = mock_groq

        res = router.generate("pm_agent", "System: PM", "User: Build real-time analytics")

        # Assertions
        assert res["status"] == "success"
        assert res["source"] == "groq_api"
        assert "openai/gpt-oss-20b (failover)" in res["model"]
        assert "Dynamic Spec from 20B Failover Engine" in res["content"]
        assert router.circuit_breaker.state == "CLOSED"

    def test_failover_120b_and_20b_to_qwen(self):
        """Simulate 429 on gpt-oss-120b AND gpt-oss-20b; verify graceful failover to qwen3.8-27b."""
        router = ModelRouter()
        router.groq_api_key = "gsk_test_mock_valid_key_1234567890"

        mock_groq = MagicMock()

        def side_effect(model, messages, **kwargs):
            if "gpt-oss" in model:
                raise Exception(f"Error code: 429 - Rate limit reached for model {model}")
            elif "qwen" in model:
                return MockGroqResponse(content="```mermaid\nflowchart TD\n  A --> B\n```\nLive Qwen synthesis.")
            raise Exception(f"Unexpected model call: {model}")

        mock_groq.chat.completions.create.side_effect = side_effect
        router.groq_client = mock_groq

        res = router.generate("architect_agent", "System: Architect", "User: Create C4 diagrams")

        assert res["status"] == "success"
        assert res["source"] == "groq_api"
        assert "qwen/qwen3.8-27b (failover)" in res["model"]
        assert "Live Qwen synthesis" in res["content"]
        assert router.circuit_breaker.state == "CLOSED"

    def test_exponential_backoff_and_retry(self):
        """Simulate 429 on attempt 0 across all models, then recovery on attempt 1.
        
        Verify exponential backoff sleep occurred and attempt 1 succeeded.
        """
        router = ModelRouter()
        router.groq_api_key = "gsk_test_mock_valid_key_1234567890"
        router.retry_backoff = 0.1  # Fast backoff for test speed

        mock_groq = MagicMock()
        attempt_tracker = {"call_count": 0}
        sleep_durations = []

        def side_effect(model, messages, **kwargs):
            attempt_tracker["call_count"] += 1
            # On attempt 0, all 3 models fail with 429
            # Attempt 0: 120b (call 1), 20b (call 2), qwen (call 3)
            if attempt_tracker["call_count"] <= 3:
                raise Exception(f"Error code: 429 - Model {model} rate limited")
            # On attempt 1: 120b succeeds!
            return MockGroqResponse(content="Recovered after backoff on gpt-oss-120b!")

        mock_groq.chat.completions.create.side_effect = side_effect
        router.groq_client = mock_groq

        with patch("time.sleep", side_effect=lambda s: sleep_durations.append(s)) as mock_sleep:
            res = router.generate("systems_agent", "System: Sys", "User: Deploy cluster")

        assert res["status"] == "success"
        assert res["model"] == "openai/gpt-oss-120b"
        assert "Recovered after backoff" in res["content"]
        assert len(sleep_durations) >= 1
        # Exponential backoff base 0.1 * 2^0 + jitter (0.1..0.4) -> approx 0.2..0.5s
        assert sleep_durations[0] >= 0.1

    def test_total_exhaustion_trips_offline_template(self):
        """Verify that when ALL models fail across ALL retries with 429, it gracefully falls back to offline template."""
        router = ModelRouter()
        router.groq_api_key = "gsk_test_mock_valid_key_1234567890"
        router.max_retries = 2
        router.retry_backoff = 0.05

        mock_groq = MagicMock()
        mock_groq.chat.completions.create.side_effect = Exception("Error code: 429 - Global Quota Exceeded")
        router.groq_client = mock_groq

        with patch("time.sleep"):
            res = router.generate("agile_agent", "System: Agile", "User: Generate sprints")

        # After all retries exhausted, it should fall back to synthesized offline blueprint
        assert res["source"] == "offline_fallback"
        assert res["status"] in ("fallback", "fallback_success")
        assert "Phase" in res["content"] or "Sprint" in res["content"] or "Task" in res["content"]
        assert router.circuit_breaker.failure_count > 0


class TestCouncilDeliberation429Resilience:
    """Empirical verification of full CouncilEngine deliberation under simulated Groq 429 errors."""

    def test_council_deliberation_under_simulated_429(self):
        """Run standard council deliberation where primary model (120b) throws 429 for all seats.
        
        Verify:
        1. All council seats fail over to gpt-oss-20b
        2. Council completes without falling back to static templates
        3. All expected artifacts (PRD, Architecture, Bundle) are produced with dynamic content
        """
        router = ModelRouter()
        router.groq_api_key = "gsk_test_mock_valid_key_1234567890"

        # Mock Groq API
        mock_groq = MagicMock()

        def dynamic_council_side_effect(model, messages, **kwargs):
            if model == "openai/gpt-oss-120b":
                raise Exception("Error code: 429 - Rate limit reached for model openai/gpt-oss-120b")
            elif model == "openai/gpt-oss-20b":
                # Find role from system prompt
                sys_prompt = messages[0]["content"] if messages else ""
                if "Product Manager" in sys_prompt:
                    return MockGroqResponse("# Dynamic PRD (20B Failover)\n## Problem Statement\nHigh-throughput voice analytics.")
                elif "System Architect" in sys_prompt:
                    return MockGroqResponse("# Dynamic Architecture (20B Failover)\n```mermaid\ngraph TD\n  Client --> Gateway\n```")
                elif "UI/UX" in sys_prompt:
                    return MockGroqResponse("# Dynamic Design (20B Failover)\nLuxury Monolith OLED styling tokens.")
                elif "Systems" in sys_prompt:
                    return MockGroqResponse("# Dynamic Systems Flow (20B Failover)\nDocker compose cluster.")
                elif "Agile" in sys_prompt:
                    return MockGroqResponse("# Dynamic Agile Tasks (20B Failover)\n- [ ] Sprint 1: Foundation")
                elif "Refiner" in sys_prompt or "Packager" in sys_prompt:
                    return MockGroqResponse("# Dynamic Master Execution Bundle (20B Failover)\nAll specifications verified.")
                return MockGroqResponse("# Dynamic Fallback Content (20B Failover)")
            raise Exception(f"Unexpected model call: {model}")

        mock_groq.chat.completions.create.side_effect = dynamic_council_side_effect
        router.groq_client = mock_groq

        engine = CouncilEngine(model_router=router)

        progress_events = []
        def progress_cb(role, data):
            progress_events.append((role, data))

        transcript = "Build a real-time event streaming voice insight platform with Redis and PostgreSQL"
        result = engine.deliberate(transcript, preset="standard", progress_callback=progress_cb)

        # 1. Output structure check
        assert "artifacts" in result, "Council result missing 'artifacts' dict"
        assert "telemetry" in result, "Council result missing 'telemetry' list"
        artifacts = result["artifacts"]

        # 2. Check all core artifacts generated
        expected_artifacts = [
            "PRD.md",
            "Architecture.md",
            "design_proposal.md",
            "Flow.md",
            "tasks.md",
            "master_execution_bundle.md"
        ]
        for art in expected_artifacts:
            assert art in artifacts, f"Council failed to produce {art}"
            content = artifacts[art]
            assert "20B Failover" in content, (
                f"Artifact {art} did not contain expected dynamic failover content! Content: {content[:200]}"
            )

        # 3. Check telemetry shows failover execution
        telemetry = result["telemetry"]
        assert len(telemetry) == 6, f"Expected 6 seats in telemetry, got {len(telemetry)}"
        for entry in telemetry:
            assert entry["status"] == "success", f"Role {entry['role']} failed: {entry}"
            assert "failover" in entry["model"], f"Role {entry['role']} did not execute via failover: {entry['model']}"
            assert entry["source"] == "groq_api", f"Role {entry['role']} fell back to static template instead of live failover!"
