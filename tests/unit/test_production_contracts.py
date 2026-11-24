"""
tests/unit/test_production_contracts.py
Tier 1: Deterministic Contract & Invariant Test Suite.

Rigorously validates production Pydantic request and response models from src/api/server.py
and core data structures from src/stt_service.py with boundary values, missing fields,
type constraints, and zero network calls.
"""

import pytest
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field, ValidationError

from src.api.server import (
    HealthResponse,
    DeliberateRequest,
    RAGQueryRequest,
    RAGIndexRequest,
    KnowledgeSearchRequest,
    COUNCIL_PRESETS,
    TrialQuotaManager,
)
from src.stt_service import STTResult


# --- Auxiliary Contract Schemas for API Verification ---

class PresetDetailContract(BaseModel):
    name: str = Field(..., min_length=1)
    roles: List[str] = Field(..., min_length=1)
    description: str = Field(..., min_length=5)


class PresetResponseContract(BaseModel):
    presets: Dict[str, PresetDetailContract]


class TrialQuotaResponseContract(BaseModel):
    monthly_used: int = Field(..., ge=0)
    monthly_limit: int = Field(..., ge=1)
    monthly_remaining: int = Field(..., ge=0)
    session_edits_used: int = Field(..., ge=0)
    session_edits_remaining: int = Field(..., ge=0)
    session_edit_limit: int = Field(..., ge=1)
    reset_in_days: int = Field(..., ge=1)


# --- Tier 1 Unit & Contract Tests ---

@pytest.mark.unit
class TestProductionContracts:
    """Rigorous unit tests for API Pydantic schemas and data contracts."""

    def test_health_response_default_values(self):
        """Verify HealthResponse default fields and serialization."""
        health = HealthResponse()
        assert health.status == "healthy"
        assert health.version == "2.0.0"
        assert health.service == "Vo-Gen-Flow"
        assert isinstance(health.groq_configured, bool)

        serialized = health.model_dump()
        assert serialized["status"] == "healthy"
        assert serialized["version"] == "2.0.0"

    def test_health_response_custom_values(self):
        """Verify HealthResponse customization."""
        health = HealthResponse(status="degraded", version="2.1.0", service="Vo-Gen-Flow-Worker", groq_configured=True)
        assert health.status == "degraded"
        assert health.version == "2.1.0"
        assert health.groq_configured is True

    def test_deliberate_request_valid_minimal(self):
        """Verify DeliberateRequest with minimal valid fields."""
        req = DeliberateRequest(transcript="Implement a distributed rate limiter in Redis")
        assert req.transcript == "Implement a distributed rate limiter in Redis"
        assert req.preset == "standard"
        assert req.engine_mode == "auto"
        assert req.session_id is None
        assert req.byok_key is None

    def test_deliberate_request_valid_full(self):
        """Verify DeliberateRequest with all valid fields."""
        req = DeliberateRequest(
            transcript="Refactor database schema for multi-tenant isolation",
            preset="security_pentest",
            byok_key="gsk_test12345678901234567890",
            session_id="session_abc-123_XYZ",
            engine_mode="groq"
        )
        assert req.preset == "security_pentest"
        assert req.session_id == "session_abc-123_XYZ"
        assert req.engine_mode == "groq"

    def test_deliberate_request_transcript_too_short(self):
        """Verify DeliberateRequest rejects transcript shorter than 3 characters."""
        with pytest.raises(ValidationError) as exc:
            DeliberateRequest(transcript="ab")
        assert "transcript" in str(exc.value)

    def test_deliberate_request_transcript_empty(self):
        """Verify DeliberateRequest rejects empty transcript."""
        with pytest.raises(ValidationError):
            DeliberateRequest(transcript="")

    def test_deliberate_request_transcript_missing(self):
        """Verify DeliberateRequest rejects omitted transcript."""
        with pytest.raises(ValidationError):
            DeliberateRequest()

    def test_deliberate_request_session_id_traversal_rejection(self):
        """Verify DeliberateRequest regex rejects path traversal characters in session_id."""
        traversal_payloads = [
            "../../etc/passwd",
            "..\\..\\windows\\system32",
            "session/../evil",
            "session id with spaces",
            "session!@#$",
            "session;rm -rf /",
        ]
        for payload in traversal_payloads:
            with pytest.raises(ValidationError):
                DeliberateRequest(transcript="Valid architectural prompt", session_id=payload)

    def test_deliberate_request_session_id_allowed_patterns(self):
        """Verify DeliberateRequest accepts valid alphanumeric, dash, and underscore session IDs."""
        valid_ids = [
            "session123",
            "sess-456",
            "sess_789",
            "SESS-123_abc-XYZ",
            "1234567890",
        ]
        for sid in valid_ids:
            req = DeliberateRequest(transcript="Valid architectural prompt", session_id=sid)
            assert req.session_id == sid

    def test_rag_index_request_valid(self):
        """Verify RAGIndexRequest accepts valid document content."""
        req = RAGIndexRequest(text="This is a valid architecture document with more than 10 characters.")
        assert len(req.text) > 10
        assert req.source_name == "custom_document.md"

    def test_rag_index_request_custom_source(self):
        """Verify RAGIndexRequest allows custom source name."""
        req = RAGIndexRequest(
            text="CREATE TABLE users (id SERIAL PRIMARY KEY, email TEXT NOT NULL);",
            source_name="schema_migration_v1.sql"
        )
        assert req.source_name == "schema_migration_v1.sql"

    def test_rag_index_request_too_short(self):
        """Verify RAGIndexRequest rejects text shorter than 10 characters."""
        with pytest.raises(ValidationError):
            RAGIndexRequest(text="too short")

    def test_rag_index_request_missing_text(self):
        """Verify RAGIndexRequest rejects missing text."""
        with pytest.raises(ValidationError):
            RAGIndexRequest()

    def test_rag_query_request_valid_minimal(self):
        """Verify RAGQueryRequest with valid minimal query."""
        req = RAGQueryRequest(query="How does rate limiting work?")
        assert req.query == "How does rate limiting work?"
        assert req.top_k == 3
        assert req.byok_key is None

    def test_rag_query_request_valid_top_k(self):
        """Verify RAGQueryRequest bounds for top_k parameter."""
        req_min = RAGQueryRequest(query="PostgreSQL schemas", top_k=1)
        assert req_min.top_k == 1

        req_max = RAGQueryRequest(query="PostgreSQL schemas", top_k=10)
        assert req_max.top_k == 10

    def test_rag_query_request_out_of_bounds_top_k(self):
        """Verify RAGQueryRequest rejects top_k outside [1, 10]."""
        with pytest.raises(ValidationError):
            RAGQueryRequest(query="Valid query", top_k=0)

        with pytest.raises(ValidationError):
            RAGQueryRequest(query="Valid query", top_k=11)

    def test_rag_query_request_query_too_short(self):
        """Verify RAGQueryRequest rejects query shorter than 2 characters."""
        with pytest.raises(ValidationError):
            RAGQueryRequest(query="a")

        with pytest.raises(ValidationError):
            RAGQueryRequest(query="")

    def test_knowledge_search_request_valid(self):
        """Verify KnowledgeSearchRequest valid schema."""
        req = KnowledgeSearchRequest(query="FastAPI", top_k=5)
        assert req.query == "FastAPI"
        assert req.top_k == 5

    def test_knowledge_search_request_bounds(self):
        """Verify KnowledgeSearchRequest rejects invalid bounds."""
        with pytest.raises(ValidationError):
            KnowledgeSearchRequest(query="a", top_k=3)  # too short

        with pytest.raises(ValidationError):
            KnowledgeSearchRequest(query="valid", top_k=0)  # ge=1

        with pytest.raises(ValidationError):
            KnowledgeSearchRequest(query="valid", top_k=15)  # le=10

    def test_stt_result_data_structure(self):
        """Verify STTResult initialization, dictionary serialization, and repr."""
        res = STTResult(
            text="Build a high performance microservices architecture",
            duration_seconds=5.25,
            latency_seconds=0.32,
            language="en",
            segments=[{"id": 0, "text": "Build a high performance"}],
            provider="groq",
            model="whisper-large-v3-turbo"
        )
        assert res.text == "Build a high performance microservices architecture"
        assert res.duration_seconds == 5.25
        assert res.latency_seconds == 0.32
        assert res.language == "en"
        assert len(res.segments) == 1

        d = res.to_dict()
        assert d["text"] == res.text
        assert d["duration_seconds"] == 5.25
        assert d["latency_seconds"] == 0.32
        assert d["segments_count"] == 1
        assert d["provider"] == "groq"
        assert d["model"] == "whisper-large-v3-turbo"

        r = repr(res)
        assert "groq" in r
        assert "whisper-large-v3-turbo" in r
        assert "text_len=" in r

    def test_stt_result_defaults(self):
        """Verify STTResult default values."""
        res = STTResult(text="Minimal audio transcript")
        assert res.duration_seconds == 0.0
        assert res.latency_seconds == 0.0
        assert res.language == "en"
        assert res.segments == []
        assert res.provider == "groq"

    def test_presets_contract_adherence(self):
        """Verify COUNCIL_PRESETS adheres strictly to PresetResponseContract."""
        validated = PresetResponseContract(presets=COUNCIL_PRESETS)
        assert "standard" in validated.presets
        assert "security_pentest" in validated.presets
        assert "lean_sprint" in validated.presets

        for name, preset in validated.presets.items():
            assert len(preset.roles) >= 1
            assert len(preset.name) >= 1
            assert len(preset.description) >= 5

    def test_trial_quota_contract_adherence(self):
        """Verify TrialQuotaManager.get_quota_status conforms to TrialQuotaResponseContract."""
        manager = TrialQuotaManager()
        status = manager.get_quota_status("127.0.0.1", session_id="test_session_1")
        validated = TrialQuotaResponseContract(**status)
        assert validated.monthly_limit == 5
        assert validated.session_edit_limit == 4
        assert validated.monthly_used >= 0
        assert validated.monthly_remaining <= validated.monthly_limit
        assert validated.reset_in_days >= 1
