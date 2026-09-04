"""Unit tests for CuratedKnowledgeDB."""

import unittest
import os
import json
import tempfile
from src.knowledge_db import CuratedKnowledgeDB


class TestCuratedKnowledgeDB(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.catalog_path = os.path.join(self.temp_dir.name, "test_catalog.json")
        sample_data = {
            "version": "2.0.0",
            "templates": [
                {
                    "id": "test_fastapi",
                    "title": "FastAPI Async Application",
                    "keywords": ["fastapi", "async", "api", "router"],
                    "description": "Async FastAPI service setup.",
                    "snippet": "app = FastAPI()"
                },
                {
                    "id": "test_postgres",
                    "title": "PostgreSQL Multi-Tenant Schema",
                    "keywords": ["postgres", "sql", "ddl", "schema", "table"],
                    "description": "Relational PostgreSQL database schema.",
                    "snippet": "CREATE TABLE tenants (id UUID PRIMARY KEY);"
                }
            ]
        }
        with open(self.catalog_path, "w", encoding="utf-8") as f:
            json.dump(sample_data, f)
        self.db = CuratedKnowledgeDB(self.catalog_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_catalog_loaded(self):
        self.assertEqual(len(self.db.templates), 2)

    def test_search_fastapi(self):
        results = self.db.search("build a fast async rest api router", top_k=1)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["id"], "test_fastapi")

    def test_search_postgres(self):
        results = self.db.search("create sql ddl database tables for tenants", top_k=1)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["id"], "test_postgres")

    def test_format_for_prompt(self):
        prompt_block = self.db.format_for_prompt("fastapi backend", top_k=1)
        self.assertIn("<curated_engineering_knowledge>", prompt_block)
        self.assertIn("test_fastapi", prompt_block)
        self.assertIn("app = FastAPI()", prompt_block)

    def test_default_catalog_exists(self):
        prod_db = CuratedKnowledgeDB()
        self.assertGreaterEqual(len(prod_db.templates), 5)


if __name__ == "__main__":
    unittest.main()
