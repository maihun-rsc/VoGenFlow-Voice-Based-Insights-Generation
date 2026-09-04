"""Curated Knowledge Base & Pattern Retriever for Vo-Gen-Flow."""

import os
import json
import math
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger("vogenflow.knowledge_db")


class CuratedKnowledgeDB:
    """In-memory Curated Engineering Knowledge Catalog with BM25 retrieval."""

    def __init__(self, catalog_path: Optional[str] = None):
        if catalog_path is None:
            # Default to data/curated_knowledge.json relative to project root
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            catalog_path = os.path.join(base_dir, "data", "curated_knowledge.json")
        self.catalog_path = catalog_path
        self.templates: List[Dict[str, Any]] = []
        self.doc_index: List[Dict[str, Any]] = []
        self.doc_lengths: List[int] = []
        self.avg_doc_length: float = 0.0
        self.vocab: Dict[str, int] = {}
        self.k1 = 1.5
        self.b = 0.75
        self.load_catalog()

    def load_catalog(self) -> None:
        """Load templates from JSON and build BM25 search indices."""
        if not os.path.exists(self.catalog_path):
            logger.warning("Curated catalog file %s not found. Using empty catalog.", self.catalog_path)
            self.templates = []
            return

        try:
            with open(self.catalog_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.templates = data.get("templates", [])
            self._build_index()
            logger.info("Loaded %d curated templates into knowledge catalog.", len(self.templates))
        except Exception as e:
            logger.error("Failed to parse curated knowledge catalog: %s", str(e))
            self.templates = []

    def _tokenize(self, text: str) -> List[str]:
        """Simple case-insensitive whitespace/punctuation tokenizer."""
        clean = ""
        for ch in text.lower():
            if ch.isalnum():
                clean += ch
            else:
                clean += " "
        return [t for t in clean.split() if len(t) > 1]

    def _build_index(self) -> None:
        """Build term frequencies and BM25 statistics for templates."""
        self.doc_index = []
        self.doc_lengths = []
        total_len = 0
        df: Dict[str, int] = {}

        for tmpl in self.templates:
            # Combine title, keywords, description, and snippet for searchable text
            combined_text = f"{tmpl.get('title', '')} {' '.join(tmpl.get('keywords', []))} {tmpl.get('description', '')} {tmpl.get('snippet', '')}"
            tokens = self._tokenize(combined_text)
            doc_len = len(tokens)
            self.doc_lengths.append(doc_len)
            total_len += doc_len

            tf: Dict[str, int] = {}
            for t in tokens:
                tf[t] = tf.get(t, 0) + 1
            self.doc_index.append(tf)

            for unique_term in tf.keys():
                df[unique_term] = df.get(unique_term, 0) + 1

        self.avg_doc_length = total_len / len(self.doc_lengths) if self.doc_lengths else 0.0

        # Compute IDF for vocabulary
        N = len(self.templates)
        self.vocab = {}
        for term, freq in df.items():
            # Standard BM25 IDF
            idf = math.log((N - freq + 0.5) / (freq + 0.5) + 1.0)
            self.vocab[term] = max(0.01, idf)

    def search(self, query: str, top_k: int = 2) -> List[Dict[str, Any]]:
        """Perform BM25 search over the curated catalog to find relevant architectural templates."""
        if not self.templates or not self.doc_index:
            return []

        q_tokens = self._tokenize(query)
        if not q_tokens:
            return self.templates[:top_k]

        scores = [0.0] * len(self.templates)

        for i, tf in enumerate(self.doc_index):
            doc_len = self.doc_lengths[i]
            score = 0.0
            for term in q_tokens:
                if term in tf:
                    term_freq = tf[term]
                    idf = self.vocab.get(term, 0.5)
                    numerator = term_freq * (self.k1 + 1.0)
                    denominator = term_freq + self.k1 * (1.0 - self.b + self.b * (doc_len / (self.avg_doc_length or 1.0)))
                    score += idf * (numerator / denominator)
            scores[i] = score

        # Rank templates by score descending
        ranked_indices = sorted(range(len(scores)), key=lambda idx: scores[idx], reverse=True)
        results = []
        for idx in ranked_indices[:top_k]:
            tmpl = dict(self.templates[idx])
            tmpl["relevance_score"] = round(scores[idx], 4)
            results.append(tmpl)

        return results

    def format_for_prompt(self, query: str, top_k: int = 2) -> str:
        """Format retrieved templates into an XML block ready for LLM prompt injection."""
        results = self.search(query, top_k=top_k)
        if not results:
            return ""

        output = ["<curated_engineering_knowledge>"]
        for item in results:
            output.append(f"  <template id=\"{item.get('id')}\" title=\"{item.get('title')}\">")
            output.append(f"    <description>{item.get('description')}</description>")
            output.append("    <reference_snippet>")
            output.append(item.get("snippet", "").strip())
            output.append("    </reference_snippet>")
            output.append("  </template>")
        output.append("</curated_engineering_knowledge>")
        return "\n".join(output)
