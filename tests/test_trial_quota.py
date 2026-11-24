"""
Test suite for Vo-Gen-Flow Trial Quota Management.
Verifies:
1. 5 monthly prompts limit per client IP.
2. Max 4 iterative edits per session.
3. HTTP 429 Too Many Requests response with clear remaining counters.
4. /api/trial/quota status reporting.
"""

import unittest
from fastapi.testclient import TestClient

import src.api.server as server_module
from src.api.server import app, trial_manager
from src.council_engine import CouncilEngine
from src.model_router import ModelRouter
from src.knowledge_db import CuratedKnowledgeDB


class TestTrialQuota(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        offline_router = ModelRouter(api_key=None, min_request_interval=0.001)
        k_db = CuratedKnowledgeDB()
        server_module.council_engine = CouncilEngine(
            model_router=offline_router, knowledge_db=k_db
        )
        server_module.knowledge_db = k_db
        cls.client = TestClient(app)

    def setUp(self):
        # Reset quotas between test runs
        trial_manager.reset()

    def test_quota_status_fresh_client(self):
        """Verify initial trial quota is 5 prompts / 0 used."""
        res = self.client.get("/api/trial/quota", headers={"x-client-id": "fresh_user_01"})
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["monthly_limit"], 5)
        self.assertEqual(data["monthly_used"], 0)
        self.assertEqual(data["monthly_remaining"], 5)
        self.assertEqual(data["session_edit_limit"], 4)

    def test_monthly_prompt_exhaustion(self):
        """Client can make 5 root prompts, 6th prompt must return HTTP 429."""
        client_headers = {"x-client-id": "quota_test_user", "x-enforce-quota": "true"}

        for i in range(5):
            res = self.client.post(
                "/api/council/deliberate",
                json={"transcript": f"Design microservice component number {i+1}", "preset": "lean_sprint"},
                headers=client_headers
            )
            self.assertEqual(res.status_code, 200, f"Prompt {i+1} should succeed")
            self.assertIn("quota", res.json())
            self.assertEqual(res.json()["quota"]["monthly_used"], i + 1)

        # 6th prompt should trigger HTTP 429
        blocked = self.client.post(
            "/api/council/deliberate",
            json={"transcript": "Design one more microservice", "preset": "lean_sprint"},
            headers=client_headers
        )
        self.assertEqual(blocked.status_code, 429)
        err_data = blocked.json()["detail"]
        self.assertEqual(err_data["error"], "quota_exceeded")
        self.assertEqual(err_data["quota"]["monthly_used"], 5)

    def test_session_iterative_edit_limits(self):
        """Within a session, client can make up to 4 iterative edits, 5th edit is blocked."""
        client_headers = {"x-client-id": "session_edit_user", "x-enforce-quota": "true"}

        # 1. Start root prompt
        root_res = self.client.post(
            "/api/council/deliberate",
            json={"transcript": "Build a multi-tenant payment gateway", "preset": "lean_sprint"},
            headers=client_headers
        )
        self.assertEqual(root_res.status_code, 200)
        session_id = root_res.json()["session_id"]

        # 2. Perform 4 iterative edits
        for edit_num in range(1, 5):
            edit_res = self.client.post(
                "/api/council/deliberate",
                json={
                    "transcript": f"Edit {edit_num}: Add webhook signature verification",
                    "preset": "lean_sprint",
                    "session_id": session_id
                },
                headers=client_headers
            )
            self.assertEqual(edit_res.status_code, 200, f"Edit {edit_num} should succeed")
            self.assertEqual(edit_res.json()["quota"]["session_edits"], edit_num)

        # 3. 5th iterative edit on the same session should trigger HTTP 429
        blocked_edit = self.client.post(
            "/api/council/deliberate",
            json={
                "transcript": "Edit 5: Refactor schema again",
                "preset": "lean_sprint",
                "session_id": session_id
            },
            headers=client_headers
        )
        self.assertEqual(blocked_edit.status_code, 429)
        err_data = blocked_edit.json()["detail"]
        self.assertEqual(err_data["error"], "quota_exceeded")
        self.assertEqual(err_data["quota"]["session_edits"], 4)


if __name__ == "__main__":
    unittest.main()
