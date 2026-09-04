import unittest
from fastapi.testclient import TestClient
import src.api.server as server_module
from src.api.server import app, compute_rms
from src.council_engine import CouncilEngine
from src.model_router import ModelRouter
from src.knowledge_db import CuratedKnowledgeDB


class TestAPIServer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Use fast offline router for automated testing to avoid remote rate limits
        offline_router = ModelRouter(api_key=None, min_request_interval=0.01)
        k_db = CuratedKnowledgeDB()
        server_module.council_engine = CouncilEngine(model_router=offline_router, knowledge_db=k_db)
        server_module.knowledge_db = k_db
        cls.client = TestClient(app)

    def test_health_endpoint(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "healthy")
        self.assertEqual(data["service"], "Vo-Gen-Flow")
        self.assertEqual(data["version"], "2.0.0")

    def test_presets_endpoint(self):
        response = self.client.get("/api/presets")
        self.assertEqual(response.status_code, 200)
        presets = response.json()["presets"]
        self.assertIn("standard", presets)
        self.assertIn("security_pentest", presets)
        self.assertIn("lean_sprint", presets)

    def test_knowledge_search_endpoint(self):
        response = self.client.post("/api/knowledge/search", json={"query": "fastapi async rest", "top_k": 2})
        self.assertEqual(response.status_code, 200)
        matches = response.json()["matches"]
        self.assertGreaterEqual(len(matches), 1)

    def test_deliberate_endpoint(self):
        payload = {
            "transcript": "Design a scalable event-driven notification service using Redis pubsub and PostgreSQL.",
            "preset": "lean_sprint"
        }
        response = self.client.post("/api/council/deliberate", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "success")
        self.assertIn("session_id", data)
        self.assertIn("artifacts", data)
        self.assertIn("PRD.md", data["artifacts"])

        # Fetch session
        session_id = data["session_id"]
        sess_resp = self.client.get(f"/api/sessions/{session_id}")
        self.assertEqual(sess_resp.status_code, 200)
        self.assertEqual(sess_resp.json()["session_id"], session_id)

    def test_rms_computation(self):
        # 16-bit silence
        silence = bytes(1024)
        self.assertEqual(compute_rms(silence), 0.0)

        # 16-bit sound wave (alternating values)
        import struct
        samples = [10000, -10000] * 256
        pcm = struct.pack(f"<{len(samples)}h", *samples)
        rms = compute_rms(pcm)
        self.assertGreater(rms, 0.0)

    def test_websocket_ping_pong(self):
        with self.client.websocket_connect("/ws/stream") as websocket:
            # First message should be connection established
            intro = websocket.receive_json()
            self.assertEqual(intro["type"], "connection_established")

            # Send ping
            websocket.send_json({"type": "ping"})
            pong = websocket.receive_json()
            self.assertEqual(pong["type"], "pong")

    def test_rag_index_and_query_endpoints(self):
        # Index a document
        doc_payload = {
            "text": "The billing pipeline uses Stripe webhooks with cryptographic HMAC signature verification and idempotency keys.",
            "source_name": "billing_spec.md"
        }
        res_idx = self.client.post("/api/rag/index", json=doc_payload)
        self.assertEqual(res_idx.status_code, 200)
        idx_data = res_idx.json()
        self.assertEqual(idx_data["status"], "indexed")
        self.assertGreaterEqual(idx_data["total_chunks"], 1)

        # Query the indexed document
        query_payload = {
            "query": "How are Stripe webhooks verified and handled in billing?",
            "top_k": 2
        }
        res_query = self.client.post("/api/rag/query", json=query_payload)
        self.assertEqual(res_query.status_code, 200)
        query_data = res_query.json()
        self.assertTrue(query_data["grounded"])
        self.assertGreaterEqual(len(query_data["citations"]), 1)
        self.assertEqual(query_data["citations"][0]["file"], "billing_spec.md")


if __name__ == "__main__":
    unittest.main()
