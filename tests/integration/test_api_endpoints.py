"""
tests/integration/test_api_endpoints.py
Tier 2: Real Integration & Contract Test Suite for FastAPI REST Endpoints.

Exercises all REST endpoints using FastAPI TestClient:
- System probes: /health, /api/engine/status, /api/presets, /api/trial/quota
- Knowledge search: /api/knowledge/search
- RAG lifecycle: /api/rag/index, /api/rag/query (Grounded vs. Architectural Advisory Fallback vs. Refusal)
- Multi-Model Council Deliberation: /api/council/deliberate (all 6 artifacts generated)
- Session persistence & retrieval: /api/sessions/{session_id}
- STT sample audio: /api/stt/sample-audio
"""

import pytest
from fastapi.testclient import TestClient
from src.api.server import app, ACTIVE_SESSIONS


@pytest.fixture(scope="module")
def client():
    """Create a TestClient with full lifespan context manager to seed services."""
    with TestClient(app) as c:
        yield c


@pytest.mark.integration
class TestSystemEndpoints:
    """Integration tests for system health, engine status, and presets."""

    def test_health_check_endpoint(self, client):
        """GET /health returns 200 with service metadata and groq configuration."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["version"] == "2.0.0"
        assert data["service"] == "Vo-Gen-Flow"
        assert "groq_configured" in data

    def test_engine_status_endpoint(self, client):
        """GET /api/engine/status returns active engine mode and backend telemetry."""
        response = client.get("/api/engine/status")
        assert response.status_code == 200
        data = response.json()
        assert "active_engine" in data
        assert data["active_engine"] in ("groq", "lm_studio", "offline_simulation")
        assert "groq" in data
        assert "lm_studio" in data
        assert "models" in data["groq"]

    def test_presets_endpoint(self, client):
        """GET /api/presets returns all available multi-model council presets."""
        response = client.get("/api/presets")
        assert response.status_code == 200
        data = response.json()
        assert "presets" in data
        presets = data["presets"]
        assert "standard" in presets
        assert "security_pentest" in presets
        assert "lean_sprint" in presets
        for key in ["standard", "security_pentest", "lean_sprint"]:
            assert "name" in presets[key]
            assert "roles" in presets[key]
            assert "description" in presets[key]

    def test_trial_quota_endpoint(self, client):
        """GET /api/trial/quota returns current usage and remaining allocation."""
        response = client.get("/api/trial/quota")
        assert response.status_code == 200
        data = response.json()
        assert "monthly_used" in data
        assert "monthly_limit" in data
        assert "monthly_remaining" in data
        assert "session_edits_used" in data
        assert "session_edits_remaining" in data
        assert "session_edit_limit" in data
        assert "reset_in_days" in data
        assert data["monthly_limit"] == 5
        assert data["session_edit_limit"] == 4


@pytest.mark.integration
class TestKnowledgeAndRAGEndpoints:
    """Integration tests for Curated Knowledge Catalog and Local RAG Engine."""

    def test_knowledge_search_valid(self, client):
        """POST /api/knowledge/search retrieves matching architecture blueprints."""
        payload = {"query": "PostgreSQL relational database schema", "top_k": 3}
        response = client.post("/api/knowledge/search", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["query"] == payload["query"]
        assert "matches" in data
        assert len(data["matches"]) > 0
        match = data["matches"][0]
        assert "title" in match
        assert "category" in match

    def test_knowledge_search_validation_error(self, client):
        """POST /api/knowledge/search rejects queries shorter than 2 chars."""
        response = client.post("/api/knowledge/search", json={"query": "x"})
        assert response.status_code == 422

    def test_rag_index_document(self, client):
        """POST /api/rag/index accepts document text and indexes into BM25."""
        payload = {
            "text": "The billing service processes credit card charges with Stripe webhooks and idempotency keys.",
            "source_name": "billing_service_spec.md"
        }
        response = client.post("/api/rag/index", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "indexed"
        assert data["source_name"] == "billing_service_spec.md"
        assert data["total_chunks"] >= 1
        assert "guardrail_telemetry" in data

    def test_rag_query_grounded(self, client):
        """POST /api/rag/query returns answer with citations for grounded topic."""
        # Query indexed billing service content
        payload = {"query": "How are billing charges and Stripe webhooks processed?", "top_k": 3}
        response = client.post("/api/rag/query", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "answer" in data
        assert "citations" in data
        assert isinstance(data["citations"], list)
        assert len(data["citations"]) > 0

    def test_rag_query_architectural_advisory_fallback(self, client):
        """POST /api/rag/query executes Advisory Fallback on open-ended architecture query without 500."""
        # Query technical topic that triggers advisory fallback to CuratedKnowledgeDB
        payload = {
            "query": "What are the recommended best practices and trade-offs for multi-region active-active failover?",
            "top_k": 3
        }
        response = client.post("/api/rag/query", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "answer" in data
        assert data.get("is_advisory") is True
        assert data.get("grounded") is False
        assert "[ARCHITECTURAL ADVISORY // SYNTHESIS]" in data["answer"]
        assert len(data.get("citations", [])) > 0

    def test_rag_query_out_of_domain_refusal(self, client):
        """POST /api/rag/query preserves strict refusal for out-of-domain queries."""
        payload = {
            "query": "astrophysics quantum dark matter telescope interstellar planetary nebula",
            "top_k": 3
        }
        response = client.post("/api/rag/query", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data.get("grounded") is False
        assert data.get("is_advisory", False) is False
        assert "Refusing to hallucinate" in data["answer"]


@pytest.mark.integration
class TestCouncilDeliberationAndSessions:
    """Integration tests for Council DAG deliberation and session persistence."""

    def test_council_deliberate_standard_preset(self, client):
        """POST /api/council/deliberate executes 6-seat Scatter-Gather DAG returning all artifacts."""
        payload = {
            "transcript": "Build a multi-tenant voice insight generation platform with WebSockets and FastAPI.",
            "preset": "standard",
            "session_id": "test_integ_sess_001"
        }
        response = client.post("/api/council/deliberate", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["session_id"] == "test_integ_sess_001"
        assert data["duration_seconds"] > 0
        assert "artifacts" in data
        assert "telemetry" in data

        # Verify all 6 mandatory artifacts are generated
        artifacts = data["artifacts"]
        mandatory_files = [
            "PRD.md",
            "Architecture.md",
            "design_proposal.md",
            "Flow.md",
            "tasks.md",
            "master_execution_bundle.md",
        ]
        for f in mandatory_files:
            assert f in artifacts, f"Missing required council artifact: {f}"
            assert len(artifacts[f]) > 20, f"Artifact {f} is empty or stub"

    def test_council_deliberate_lean_sprint_preset(self, client):
        """POST /api/council/deliberate executes with lean_sprint preset."""
        payload = {
            "transcript": "Create a minimal CRUD endpoint for customer feedback.",
            "preset": "lean_sprint",
            "session_id": "test_integ_lean_002"
        }
        response = client.post("/api/council/deliberate", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "artifacts" in data
        assert "master_execution_bundle.md" in data["artifacts"]

    def test_get_session_by_id_success(self, client):
        """GET /api/sessions/{session_id} retrieves persisted council session."""
        response = client.get("/api/sessions/test_integ_sess_001")
        assert response.status_code == 200
        data = response.json()
        assert data["session_id"] == "test_integ_sess_001"
        assert "artifacts" in data
        assert "transcript" in data
        assert "saved_paths" in data

    def test_get_session_not_found(self, client):
        """GET /api/sessions/{session_id} returns 404 for unknown session ID."""
        response = client.get("/api/sessions/nonexistent_session_9999")
        assert response.status_code == 404
        assert response.json()["detail"] == "Session not found"

    def test_get_session_invalid_format_rejected(self, client):
        """GET /api/sessions/{session_id} rejects directory traversal with 400."""
        response = client.get("/api/sessions/..%2F..%2Fetc%2Fpasswd")
        assert response.status_code in (400, 404)

    def test_get_sample_audio_endpoint(self, client):
        """GET /api/stt/sample-audio returns audio file or 404 if not present on server."""
        response = client.get("/api/stt/sample-audio")
        assert response.status_code in (200, 404)
        if response.status_code == 200:
            assert response.headers["content-type"] in ("audio/wav", "audio/x-wav")
