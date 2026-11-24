"""
tests/test_challenger_rag.py
Empirical Challenger 2: RAG Query Handling Verification.

Tests:
1. In-domain architectural queries with 0 local codebase chunk overlap:
   - Must return [ARCHITECTURAL ADVISORY // SYNTHESIS] prefix
   - Must provide constructive, non-empty architectural guidance
   - Must return is_advisory=True, grounded=False
   - Must cite curated blueprints
2. Out-of-domain non-architectural queries:
   - Must trigger strict refusal guardrail
   - Must NOT hallucinate answers
   - Must return is_advisory=False, grounded=False
   - Must contain refusal warning
"""

import os
import pytest
from pathlib import Path
from fastapi.testclient import TestClient

from src.rag_engine import LocalRAGEngine
from src.knowledge_db import CuratedKnowledgeDB
from src.api.server import app

ROOT_DIR = Path(__file__).resolve().parent.parent


@pytest.fixture(scope="module")
def rag_engine_empty_index():
    """RAG Engine with an empty index (guaranteed 0 local chunk overlap)."""
    engine = LocalRAGEngine(min_relevance_threshold=0.35)
    # Empty chunks guarantees 0 local codebase chunk overlap
    engine.clear()
    return engine


@pytest.fixture(scope="module")
def rag_engine_indexed():
    """RAG Engine indexed with standard docs."""
    engine = LocalRAGEngine(min_relevance_threshold=0.35)
    engine.clear()
    # Index only docs directory
    engine.index_directory(str(ROOT_DIR / "docs"))
    return engine


@pytest.fixture(scope="module")
def api_client():
    """FastAPI TestClient for REST endpoint verification."""
    return TestClient(app)


class TestRAGArchitecturalAdvisoryZeroOverlap:
    """Empirical verification of in-domain architectural advisory fallback with 0 chunk overlap."""

    IN_DOMAIN_ADVISORY_QUERIES = [
        "What are the recommended best practices and trade-offs for multi-region active-active failover?",
        "How should we design a distributed event-driven CQRS data pipeline with Kafka and Redis caching?",
        "What is the recommended microservice scalability pattern for database sharding and read replicas?",
        "How to architect a zero-trust Kubernetes API gateway with mutual TLS and rate limiting?",
        "How should we design high-throughput asynchronous message queues for banking transactions?"
    ]

    @pytest.mark.parametrize("query", IN_DOMAIN_ADVISORY_QUERIES)
    def test_rag_empty_index_advisory_fallback(self, rag_engine_empty_index, query):
        """With 0 indexed chunks, architectural queries must yield [ARCHITECTURAL ADVISORY // SYNTHESIS] and guidance."""
        assert len(rag_engine_empty_index.chunks) == 0, "Precondition failed: chunks must be 0"

        res = rag_engine_empty_index.query_document(query)

        # 1. Flag checks
        assert res.get("grounded") is False, "Expected grounded=False for 0 local chunk overlap"
        assert res.get("is_advisory") is True, f"Expected is_advisory=True for query: {query}"

        # 2. Prefix check
        answer = res.get("answer", "")
        assert "[ARCHITECTURAL ADVISORY // SYNTHESIS]" in answer, (
            f"Missing '[ARCHITECTURAL ADVISORY // SYNTHESIS]' prefix in answer for query: {query}"
        )

        # 3. Non-empty constructive content check
        assert len(answer.strip()) > 100, f"Advisory answer too brief (<100 chars): {answer}"
        assert ("Architectural Advisory" in answer or "Recommended Architectural Pattern" in answer or "best practices" in answer.lower()), (
            f"Advisory answer does not contain constructive guidance: {answer}"
        )

        # 4. Citations check
        citations = res.get("citations", [])
        assert len(citations) > 0, "Advisory response must provide curated blueprint citations"

    @pytest.mark.parametrize("query", IN_DOMAIN_ADVISORY_QUERIES)
    def test_api_rest_rag_advisory_fallback(self, api_client, query):
        """POST /api/rag/query must return 200 with advisory synthesis for architectural queries with 0/low overlap."""
        response = api_client.post("/api/rag/query", json={"query": query, "top_k": 3})
        assert response.status_code == 200, f"API returned {response.status_code}: {response.text}"
        data = response.json()

        # Check answer format
        answer = data.get("answer", "")
        assert "[ARCHITECTURAL ADVISORY // SYNTHESIS]" in answer or data.get("is_advisory") is True, (
            f"API response failed advisory check for query: {query}. Data: {data}"
        )
        assert len(answer) > 80


class TestRAGOutOfDomainStrictRefusal:
    """Empirical verification of strict refusal guardrail for out-of-domain queries."""

    OUT_OF_DOMAIN_QUERIES = [
        "How to bake a sourdough chocolate cake with vanilla frosting recipe?",
        "astrophysics quantum dark matter telescope interstellar planetary nebula",
        "What are the symptoms and treatments of seasonal allergic rhinitis?",
        "Who won the 1994 FIFA World Cup soccer championship final match in Pasadena?",
        "French grammar rules for irregular subjunctive verbs and past participles"
    ]

    @pytest.mark.parametrize("query", OUT_OF_DOMAIN_QUERIES)
    def test_rag_empty_index_strict_refusal(self, rag_engine_empty_index, query):
        """With 0 indexed chunks, out-of-domain queries must be strictly refused with zero hallucination."""
        res = rag_engine_empty_index.query_document(query)

        # 1. Flag checks
        assert res.get("grounded") is False, "Expected grounded=False for out-of-domain query"
        assert res.get("is_advisory", False) is False, f"Out-of-domain query should NOT be classified as advisory: {query}"

        # 2. Refusal message check
        answer = res.get("answer", "")
        assert "Refusing to hallucinate" in answer or "Guardrail Notice: No sufficiently grounded context found" in answer, (
            f"Expected strict refusal guardrail notice, but got: {answer}"
        )
        assert "[ARCHITECTURAL ADVISORY // SYNTHESIS]" not in answer, (
            f"Advisory prefix must NOT appear for out-of-domain query: {query}"
        )

    @pytest.mark.parametrize("query", OUT_OF_DOMAIN_QUERIES)
    def test_api_rest_out_of_domain_refusal(self, api_client, query):
        """POST /api/rag/query must return 200 with strict refusal for out-of-domain queries."""
        response = api_client.post("/api/rag/query", json={"query": query, "top_k": 3})
        assert response.status_code == 200
        data = response.json()

        assert data.get("grounded") is False
        assert data.get("is_advisory", False) is False
        answer = data.get("answer", "")
        assert "Refusing to hallucinate" in answer or "Guardrail Notice" in answer
        assert "[ARCHITECTURAL ADVISORY // SYNTHESIS]" not in answer
