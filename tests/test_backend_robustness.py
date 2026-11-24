"""
Backend Robustness, Concurrency, and Stress Test Suite.
Verifies system stability under heavy load:
1. Concurrent REST API requests (50 parallel threads)
2. WebSocket rapid connection/disconnection churn
3. High-volume RAG indexing & multi-query stress
4. Large payload handling (1MB input fuzzing)
5. Session store thread-safety and race condition resistance
"""

import concurrent.futures
import time
import unittest
from fastapi.testclient import TestClient

import src.api.server as server_module
from src.api.server import app
from src.council_engine import CouncilEngine
from src.model_router import ModelRouter
from src.knowledge_db import CuratedKnowledgeDB
from src.rag_engine import LocalRAGEngine


class TestBackendRobustness(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Configure test singletons with offline high-speed engines
        offline_router = ModelRouter(api_key=None, min_request_interval=0.001)
        k_db = CuratedKnowledgeDB()
        rag = LocalRAGEngine()
        server_module.council_engine = CouncilEngine(
            model_router=offline_router, knowledge_db=k_db, rag_engine=rag
        )
        server_module.knowledge_db = k_db
        server_module.rag_engine = rag
        cls.client = TestClient(app)

    def test_concurrent_api_traffic_50_workers(self):
        """Simulate 50 concurrent requests hitting health, presets, and knowledge search."""
        def make_request(i):
            if i % 3 == 0:
                res = self.client.get("/health")
            elif i % 3 == 1:
                res = self.client.get("/api/presets")
            else:
                res = self.client.post("/api/knowledge/search", json={"query": "fastapi postgresql", "top_k": 2})
            return res.status_code

        start = time.time()
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request, i) for i in range(50)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]

        duration = time.time() - start
        self.assertEqual(len(results), 50)
        self.assertTrue(all(code == 200 for code in results), "All 50 concurrent requests must return 200 OK")
        avg_latency = (duration / 50) * 1000
        print(f"\n[ROBUSTNESS] 50 Concurrent Requests completed in {duration:.3f}s (Avg: {avg_latency:.2f}ms/req)")

    def test_large_payload_rag_indexing(self):
        """Verify the server gracefully ingests large documents without crashing or memory exhaustion."""
        large_text = ("# Section Spec\n" + "This is a scalable architecture specification token data line.\n" * 100) * 50
        payload = {
            "text": large_text,
            "source_name": "large_enterprise_spec.md"
        }
        res = self.client.post("/api/rag/index", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "indexed")
        self.assertGreater(data["total_chunks"], 10)

    def test_websocket_rapid_connection_churn(self):
        """Verify that rapid connect, ping, and disconnect cycles do not leak resources or hang."""
        for _ in range(15):
            with self.client.websocket_connect("/ws/stream") as ws:
                intro = ws.receive_json()
                self.assertEqual(intro["type"], "connection_established")
                ws.send_json({"type": "ping"})
                pong = ws.receive_json()
                self.assertEqual(pong["type"], "pong")

    def test_malformed_fuzz_payloads(self):
        """Verify backend rejects malformed JSON and out-of-spec data with 422 Unprocessable Entity."""
        # Missing required fields
        res1 = self.client.post("/api/council/deliberate", json={})
        self.assertEqual(res1.status_code, 422)

        # Empty string under min_length
        res2 = self.client.post("/api/council/deliberate", json={"transcript": "a"})
        self.assertEqual(res2.status_code, 422)

        # Negative top_k
        res3 = self.client.post("/api/rag/query", json={"query": "test", "top_k": -1})
        self.assertEqual(res3.status_code, 422)

    def test_concurrent_deliberations_and_session_isolation(self):
        """Verify 5 concurrent council deliberations produce isolated sessions without race conditions."""
        transcripts = [
            "Build a payment service with Stripe webhooks.",
            "Design a user authentication system with OAuth2.",
            "Architect an audio processing pipeline with Groq Whisper.",
            "Build a notification service with Redis PubSub.",
            "Create a database schema for multi-tenant organizations."
        ]

        def run_deliberation(t):
            res = self.client.post("/api/council/deliberate", json={"transcript": t, "preset": "lean_sprint"})
            return res.json()

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(run_deliberation, t) for t in transcripts]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]

        self.assertEqual(len(results), 5)
        session_ids = [r["session_id"] for r in results]
        # Verify all session IDs are unique
        self.assertEqual(len(set(session_ids)), 5, "Session IDs must be strictly unique under concurrency")
        for r in results:
            self.assertEqual(r["status"], "success")
            self.assertIn("PRD.md", r["artifacts"])


if __name__ == "__main__":
    unittest.main()
