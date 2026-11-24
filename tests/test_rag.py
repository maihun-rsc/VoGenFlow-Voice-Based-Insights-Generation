"""
Unit Tests for Local RAG Engine
Verifies document chunking, inverted index construction, BM25 scoring, and query decomposition.
"""

import unittest
from src.rag_engine import (
    LocalRAGEngine,
    DocumentChunk,
    SemanticQueryExpander,
    LMStudioEmbeddingClient,
    reciprocal_rank_fusion,
)


class TestLocalRAGEngine(unittest.TestCase):

    def setUp(self):
        self.rag = LocalRAGEngine(top_k=2, chunk_size=50, overlap=10)

    def test_indexing_and_bm25_retrieval(self):
        doc1 = """
        # Authentication Service
        We use OAuth2 and JWT bearer tokens for secure user authentication.
        Tokens expire in 3600 seconds and are signed with RS256.
        """
        doc2 = """
        # Database Storage Layer
        PostgreSQL database with SQLAlchemy ORM models.
        Connection pooling with 10 max overflow connections.
        """
        self.rag.index_text(doc1, source_name="auth.md")
        self.rag.index_text(doc2, source_name="db.md")

        self.assertEqual(len(self.rag.chunks), 2)

        # Search for JWT Auth
        results = self.rag.search("JWT user authentication token", top_k=1)
        self.assertTrue(len(results) > 0)
        top_chunk, score = results[0]
        self.assertEqual(top_chunk.source_path, "auth.md")
        self.assertIn("OAuth2", top_chunk.content)

        # Search for Postgres Database
        results_db = self.rag.search("PostgreSQL SQLAlchemy connection", top_k=1)
        self.assertTrue(len(results_db) > 0)
        self.assertEqual(results_db[0][0].source_path, "db.md")

    def test_query_decomposition(self):
        transcript = (
            "We need to build a system that connects to our database schema "
            "and also implements an API endpoint for JWT authentication."
        )
        queries = self.rag.decompose_query(transcript)
        self.assertTrue(len(queries) >= 1)


class TestSemanticQueryExpander(unittest.TestCase):

    def setUp(self):
        self.expander = SemanticQueryExpander()

    def test_domain_keyword_extraction(self):
        text = "We want real-time streaming audio and oauth2 auth for postgresql database"
        keywords = self.expander.extract_domain_keywords(text)
        self.assertIn("real-time streaming", keywords)
        self.assertIn("auth", keywords)
        self.assertIn("database", keywords)

    def test_taxonomy_expansion(self):
        # 1. Real-time streaming
        exp1 = self.expander.expand("real-time streaming")
        self.assertIn("websockets", exp1)
        self.assertIn("sse", exp1)
        self.assertIn("duplex", exp1)
        self.assertIn("audio", exp1)
        self.assertIn("pcm", exp1)

        # 2. Auth
        exp2 = self.expander.expand("auth")
        self.assertIn("oauth2", exp2)
        self.assertIn("jwt", exp2)
        self.assertIn("rbac", exp2)
        self.assertIn("session", exp2)
        self.assertIn("tokens", exp2)

        # 3. Database
        exp3 = self.expander.expand("database")
        self.assertIn("postgresql", exp3)
        self.assertIn("schemas", exp3)
        self.assertIn("tables", exp3)
        self.assertIn("migrations", exp3)
        self.assertIn("foreign keys", exp3)

    def test_out_of_domain_no_expansion(self):
        text = "how to bake delicious chocolate chip cookies with butter and sugar"
        expanded = self.expander.expand(text)
        self.assertEqual(expanded, text)

    def test_model_router_fast_tier_query(self):
        class MockModelRouter:
            def generate(self, tier, system, user, max_tokens=60):
                return {"content": "redis celery bullmq"}

        expander = SemanticQueryExpander(model_router=MockModelRouter())
        res = expander.expand("Need async background workers")
        self.assertIn("redis celery bullmq", res)

    def test_model_router_error_fallback(self):
        class FailingRouter:
            def generate(self, *args, **kwargs):
                raise RuntimeError("Network down")

        expander = SemanticQueryExpander(model_router=FailingRouter())
        res = expander.expand("auth")
        self.assertIn("jwt", res)


class TestLMStudioEmbeddingClient(unittest.TestCase):

    def setUp(self):
        self.client = LMStudioEmbeddingClient(
            endpoint="http://127.0.0.1:1234/v1/embeddings",
            probe_timeout=0.05
        )

    def test_probe_timeout_sub_100ms_when_offline(self):
        import time
        t0 = time.time()
        is_avail = self.client.is_available(force_refresh=True)
        elapsed_ms = (time.time() - t0) * 1000.0
        self.assertFalse(is_avail)
        self.assertLess(elapsed_ms, 100.0, "Probe must complete in under 100ms")

    def test_offline_graceful_fallback(self):
        self.client._is_available = False
        self.assertIsNone(self.client.get_embedding("test"))
        self.assertIsNone(self.client.get_embeddings(["test1", "test2"]))
        res = self.client.similarity_search("test", [])
        self.assertEqual(res, [])

    def test_cosine_similarity(self):
        v1 = [1.0, 0.0, 0.0]
        v2 = [1.0, 0.0, 0.0]
        v3 = [0.0, 1.0, 0.0]
        v4 = [-1.0, 0.0, 0.0]

        # Identical
        self.assertAlmostEqual(LMStudioEmbeddingClient.cosine_similarity(v1, v2), 1.0, places=5)
        # Orthogonal
        self.assertAlmostEqual(LMStudioEmbeddingClient.cosine_similarity(v1, v3), 0.0, places=5)
        # Opposite
        self.assertAlmostEqual(LMStudioEmbeddingClient.cosine_similarity(v1, v4), -1.0, places=5)
        # Empty / mismatched
        self.assertEqual(LMStudioEmbeddingClient.cosine_similarity([], v1), 0.0)
        self.assertEqual(LMStudioEmbeddingClient.cosine_similarity(v1, [1.0]), 0.0)

    def test_similarity_search_with_mock_embeddings(self):
        chunk1 = DocumentChunk("a.md", 0, "first chunk")
        chunk1.embedding = [1.0, 0.0, 0.0]
        chunk2 = DocumentChunk("b.md", 1, "second chunk")
        chunk2.embedding = [0.8, 0.6, 0.0]
        chunk3 = DocumentChunk("c.md", 2, "third chunk")
        chunk3.embedding = [0.0, 1.0, 0.0]

        self.client._is_available = True
        self.client.get_embedding = lambda q: [1.0, 0.0, 0.0]

        results = self.client.similarity_search("query", [chunk1, chunk2, chunk3], top_k=2)
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0][0].source_path, "a.md")
        self.assertAlmostEqual(results[0][1], 1.0, places=4)
        self.assertEqual(results[1][0].source_path, "b.md")
        self.assertAlmostEqual(results[1][1], 0.8, places=4)


class TestReciprocalRankFusion(unittest.TestCase):

    def test_rrf_scoring_formula(self):
        # Item 1 at rank 1 in BM25: 1 / (60 + 1)
        # Item 1 at rank 1 in Dense: 1 / (60 + 1)
        # Total = 2 / 61
        bm25_ranks = [("doc1", 2.5), ("doc2", 1.8)]
        dense_ranks = [("doc1", 0.95), ("doc3", 0.85)]
        k = 60

        fused = reciprocal_rank_fusion(bm25_ranks, dense_ranks, k=k)
        self.assertEqual(len(fused), 3)

        # doc1 should be #1
        self.assertEqual(fused[0][0], "doc1")
        expected_doc1_score = (1.0 / (60 + 1)) + (1.0 / (60 + 1))
        self.assertAlmostEqual(fused[0][1], expected_doc1_score, places=6)

        # doc2 was rank 2 in BM25: 1 / (60 + 2) = 1/62
        # doc3 was rank 2 in Dense: 1 / (60 + 2) = 1/62
        expected_rank2_score = 1.0 / (60 + 2)
        doc2_score = next(s for d, s in fused if d == "doc2")
        doc3_score = next(s for d, s in fused if d == "doc3")
        self.assertAlmostEqual(doc2_score, expected_rank2_score, places=6)
        self.assertAlmostEqual(doc3_score, expected_rank2_score, places=6)

    def test_rrf_empty_inputs(self):
        fused = reciprocal_rank_fusion([], [])
        self.assertEqual(fused, [])

        bm25_only = [("docA", 1.0)]
        fused_bm25 = reciprocal_rank_fusion(bm25_only, [])
        self.assertEqual(len(fused_bm25), 1)
        self.assertEqual(fused_bm25[0][0], "docA")
        self.assertAlmostEqual(fused_bm25[0][1], 1.0 / 61, places=6)


class TestDualAdapterRAG(unittest.TestCase):

    def test_dual_adapter_active_fusion(self):
        rag = LocalRAGEngine(top_k=2)
        doc1 = "# WebSockets Realtime Streaming\nBidirectional audio streaming with low latency."
        doc2 = "# PostgreSQL Database Storage\nRelational schema with ACID transactions."
        rag.index_text(doc1, source_name="stream.md")
        rag.index_text(doc2, source_name="db.md")

        # Mock embedding client where LM Studio is available
        mock_client = LMStudioEmbeddingClient()
        mock_client._is_available = True

        chunk_stream = rag.chunks[0]
        chunk_db = rag.chunks[1]

        def mock_similarity_search(query, chunks, top_k=None, min_similarity=None):
            return [(chunk_db, 0.99), (chunk_stream, 0.50)]

        mock_client.similarity_search = mock_similarity_search
        rag.embedding_client = mock_client

        results = rag.search("streaming audio", top_k=2)
        self.assertEqual(len(results), 2)
        self.assertGreater(results[0][1], 0.0)

    def test_dual_adapter_offline_bm25_fallback(self):
        rag = LocalRAGEngine(top_k=2)
        doc = "# Authentication Service\nOAuth2 and JWT token authentication."
        rag.index_text(doc, source_name="auth.md")

        # Embedding client is offline
        rag.embedding_client._is_available = False
        results = rag.search("OAuth2 JWT authentication", top_k=1)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0][0].source_path, "auth.md")
        self.assertGreater(results[0][1], 0.1)


if __name__ == "__main__":
    unittest.main()
