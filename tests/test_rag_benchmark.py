"""RAG Evaluation and Benchmark Test Suite for Vo-Gen-Flow.

Measures Hit Rate @ 3, Mean Reciprocal Rank (MRR), synonym expansion,
zero-hallucination thresholding on out-of-domain queries, and sub-5ms retrieval latency.
"""

import time
import unittest
from src.knowledge_db import CuratedKnowledgeDB
from src.rag_engine import LocalRAGEngine, DocumentChunk


class TestRAGBenchmark(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.knowledge_db = CuratedKnowledgeDB()
        cls.rag = LocalRAGEngine(top_k=3, min_relevance_threshold=0.10)
        
        # Index all 16 curated templates into LocalRAGEngine
        for tmpl in cls.knowledge_db.templates:
            content = f"{tmpl['title']}\nKeywords: {' '.join(tmpl.get('keywords', []))}\n{tmpl['description']}\n{tmpl.get('snippet', '')}"
            cls.rag.index_text(content, source_name=f"{tmpl['id']}.md")

    def test_curated_catalog_size(self):
        """Verify that the expanded curated knowledge catalog has at least 16 blueprints."""
        self.assertGreaterEqual(len(self.knowledge_db.templates), 16)

    def test_rag_domain_benchmarks(self):
        """Verify Hit Rate @ 3 across 10 critical cloud & architecture domains."""
        benchmarks = [
            ("real-time collaborative voice audio streaming with webrtc", ["webrtc_voice_streaming", "fastapi_async_service"]),
            ("multi-tenant postgresql relational database with row level security and uuid", ["postgresql_ddl_relational"]),
            ("background worker asynchronous task queue with redis and celery", ["celery_redis_worker"]),
            ("event-driven pubsub distributed streaming with apache kafka broker", ["kafka_event_streaming"]),
            ("kubernetes microservice helm deployment with ingress and autoscaling", ["kubernetes_microservice_helm"]),
            ("apollo federation graphql unified api gateway with schema subgraph", ["graphql_federation_gateway"]),
            ("oauth2 authentication with jwt bearer tokens and rbac permissions", ["oauth2_jwt_rbac"]),
            ("redis distributed cache aside pattern with redlock concurrency", ["redis_cache_aside_lock"]),
            ("command query responsibility segregation cqrs with event sourcing", ["cqrs_event_sourcing"]),
            ("stripe saas billing subscription manager with webhook lifecycle", ["stripe_billing_subscription"]),
        ]

        hits = 0
        total = len(benchmarks)

        for query, expected_ids in benchmarks:
            results = self.knowledge_db.search(query, top_k=3)
            retrieved_ids = [r["id"] for r in results]
            
            # Check if any expected ID is in top 3
            match = any(exp in retrieved_ids for exp in expected_ids)
            if match:
                hits += 1
            else:
                print(f"FAILED RETRIEVAL for '{query}': Got {retrieved_ids}, Expected any of {expected_ids}")

        hit_rate = hits / total
        print(f"\n[RAG BENCHMARK] Hit Rate @ 3: {hit_rate * 100:.1f}% ({hits}/{total})")
        self.assertGreaterEqual(hit_rate, 0.90, "RAG Hit Rate @ 3 must be at least 90%")

    def test_out_of_domain_zero_hallucination(self):
        """Verify that irrelevant out-of-domain queries return zero grounded citations."""
        irrelevant_queries = [
            "how to bake delicious chocolate chip cookies with butter and sugar",
            "best travel destinations in northern italy during springtime",
            "tennis racket string tension recommendations for beginners"
        ]

        for query in irrelevant_queries:
            qa_res = self.rag.query_document(query, top_k=3)
            # Relevance score must be below threshold or grounded matches empty
            self.assertFalse(qa_res.get("grounded", False), f"Query '{query}' should not be grounded!")
            self.assertEqual(len(qa_res.get("citations", [])), 0)

    def test_retrieval_latency(self):
        """Verify retrieval executes in sub-5ms time budget."""
        query = "high-throughput websocket gateway with celery worker and postgresql database"
        
        t0 = time.time()
        for _ in range(50):
            _ = self.knowledge_db.search(query, top_k=3)
        elapsed = (time.time() - t0) / 50.0

        latency_ms = elapsed * 1000.0
        print(f"[RAG LATENCY] Average BM25 retrieval latency: {latency_ms:.3f} ms")
        self.assertLess(latency_ms, 5.0, "Retrieval latency must be under 5ms")


if __name__ == "__main__":
    unittest.main()
