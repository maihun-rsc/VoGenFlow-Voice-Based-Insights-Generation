"""
RAG Engine (Retrieval-Augmented Generation) Module
Provides local document indexing, chunking, semantic keyword/BM25 retrieval, query decomposition,
grounded context injection, and an interactive Document Query system with enterprise security guardrails.
"""

import math
import os
import re
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

logger = logging.getLogger("vogenflow.rag_engine")

# Guardrail: Sensitive file patterns and paths excluded from indexing
SENSITIVE_PATTERNS = [
    r"\.env(\..+)?$",
    r".*secret.*",
    r".*credential.*",
    r".*token.*",
    r"id_rsa.*",
    r".*\.pem$",
    r".*\.key$",
    r".*\.cert$",
    r".*\.pfx$",
    r".*\.p12$",
    r".*\.kdbx$",
    r".*\.sqlite3?$",
    r".*\.db$",
    r".*\.pyc$",
    r".*\.log$",
]

EXCLUDED_DIRECTORIES = {
    ".git", ".svn", ".hg", ".venv", "venv", "node_modules",
    "__pycache__", ".idea", ".vscode", "dist", "build", "output"
}

# Guardrail: Indirect Prompt Injection Patterns
INDIRECT_INJECTION_PATTERNS = [
    r"<\/?(system|user|assistant|user_prompt|admin|eval|context)[^>]*>",
    r"ignore\s+(all\s+)?previous\s+instructions",
    r"disregard\s+(all\s+)?prior\s+prompts",
    r"output\s+(the\s+)?admin\s+password",
    r"admin\s+password",
    r"dump\s+(all\s+)?environment\s+variables",
    r"system\s+compromised",
    r"disregard\s+prd",
    r"write\s+malware",
    r"malware",
    r"\b(?:select\s+\*\s+from|drop\s+table|delete\s+from)\b",
    r"<script\b[^>]*>.*?<\/script>",
]


def is_sensitive_file(file_path: str) -> bool:
    """Guardrail Check: Determine if a file path matches known secrets or credentials."""
    name = Path(file_path).name.lower()
    for pat in SENSITIVE_PATTERNS:
        if re.match(pat, name, re.IGNORECASE):
            return True
    return False


def sanitize_document_content(content: str) -> Tuple[str, bool]:
    """Guardrail: Cleanse document text of indirect prompt injections and fence breakouts.
    
    Returns:
        (sanitized_text, was_modified)
    """
    if not content:
        return "", False
        
    original = content
    cleaned = content

    # 1. Neutralize injection patterns
    for pat in INDIRECT_INJECTION_PATTERNS:
        cleaned = re.sub(pat, "[SECURITY_REDACTED]", cleaned, flags=re.IGNORECASE | re.DOTALL)

    # 2. Escape role spoofing prefixes (including indented lines)
    cleaned = re.sub(r"(?m)^\s*(System|Assistant|Admin|Human|Operator)\s*:\s*", r"[\1_Note]: ", cleaned)

    # 3. Guard against unclosed markdown code fences
    fence_count = len(re.findall(r"^```", cleaned, flags=re.MULTILINE))
    if fence_count % 2 != 0:
        cleaned += "\n```\n"

    was_modified = cleaned != original
    return cleaned, was_modified


ENGLISH_STOP_WORDS = {
    "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "with",
    "by", "from", "of", "about", "as", "into", "through", "during", "before", "after",
    "above", "below", "between", "under", "again", "further", "then", "once",
    "is", "are", "was", "were", "be", "been", "being", "have", "has", "had",
    "do", "does", "did", "doing", "how", "what", "which", "who", "whom", "when",
    "where", "why", "all", "any", "both", "each", "few", "more", "most", "other",
    "some", "such", "no", "nor", "not", "only", "own", "same", "so", "than", "too",
    "very", "can", "could", "will", "would", "should", "shall", "may", "might", "must",
    "it", "its", "this", "that", "these", "those", "i", "me", "my", "we", "our",
    "you", "your", "he", "him", "his", "she", "her", "they", "them", "their"
}


class DocumentChunk:
    """Represents a chunk of indexed technical documentation or code."""

    def __init__(self, source_path: str, chunk_id: int, content: str, title: str = ""):
        self.source_path = source_path
        self.chunk_id = chunk_id
        self.content = content.strip()
        self.title = title or Path(source_path).name
        self.tokens: List[str] = self._tokenize(self.content)

    @staticmethod
    def _tokenize(text: str) -> List[str]:
        """Convert text into normalized lowercase alphanumeric tokens, filtering stop words."""
        raw_tokens = re.findall(r"\b[a-zA-Z0-9_\-\.]{2,}\b", text.lower())
        filtered = [t for t in raw_tokens if t not in ENGLISH_STOP_WORDS]
        return filtered if filtered else raw_tokens


class LocalRAGEngine:
    """Lightweight, self-contained RAG and semantic retrieval engine with enterprise guardrails."""

    def __init__(self, top_k: int = 4, chunk_size: int = 400, overlap: int = 50, min_relevance_threshold: float = 0.1):
        self.top_k = top_k
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.min_relevance_threshold = min_relevance_threshold
        self.chunks: List[DocumentChunk] = []
        self.doc_freqs: Dict[str, int] = {}
        self.total_docs: int = 0
        self.avg_doc_len: float = 0.0
        self.blocked_sensitive_files: int = 0
        self.sanitized_injections_count: int = 0

    def clear(self):
        """Reset the index and guardrail metrics."""
        self.chunks = []
        self.doc_freqs = {}
        self.total_docs = 0
        self.avg_doc_len = 0.0
        self.blocked_sensitive_files = 0
        self.sanitized_injections_count = 0

    def index_directory(self, dir_path: str, file_extensions: Optional[List[str]] = None) -> int:
        """Scan a directory and index all matching code and document files, skipping sensitive paths."""
        if file_extensions is None:
            file_extensions = [".md", ".py", ".txt", ".json", ".yaml", ".yml", ".ts", ".js", ".sql", ".rst"]

        indexed_files = 0
        path = Path(dir_path)
        if not path.exists():
            return 0

        for root, dirs, files in os.walk(path):
            # Guardrail: Prune excluded directories
            dirs[:] = [d for d in dirs if d not in EXCLUDED_DIRECTORIES and not d.startswith(".")]

            for file in files:
                full_path = os.path.join(root, file)
                # Guardrail: Check for sensitive file patterns first
                if is_sensitive_file(full_path):
                    self.blocked_sensitive_files += 1
                    logger.warning("RAG Guardrail blocked sensitive file: %s", full_path)
                    continue

                ext = Path(file).suffix.lower()
                if ext in file_extensions:
                    try:
                        if self.index_file(full_path):
                            indexed_files += 1
                    except Exception as e:
                        logger.warning("Error indexing file %s: %s", full_path, str(e))
                        continue

        self._recompute_bm25_stats()
        return indexed_files

    def index_text(self, text: str, source_name: str = "custom_context"):
        """Index raw text directly into chunks with prompt injection sanitization."""
        # Guardrail: Sanitize text
        clean_text, was_modified = sanitize_document_content(text)
        if was_modified:
            self.sanitized_injections_count += 1
            logger.info("RAG Guardrail sanitized indirect prompt injection in text '%s'", source_name)

        words = clean_text.split()
        if not words:
            return

        chunk_id = 0
        step = max(1, self.chunk_size - self.overlap)
        for i in range(0, len(words), step):
            chunk_words = words[i : i + self.chunk_size]
            chunk_content = " ".join(chunk_words)
            if len(chunk_content.strip()) > 20:
                chunk = DocumentChunk(
                    source_path=source_name,
                    chunk_id=chunk_id,
                    content=chunk_content,
                    title=source_name,
                )
                self.chunks.append(chunk)
                chunk_id += 1

        self._recompute_bm25_stats()

    def index_file(self, file_path: str) -> bool:
        """Chunk and index a single file with guardrail verification."""
        # Guardrail: Check for sensitive file patterns
        if is_sensitive_file(file_path):
            self.blocked_sensitive_files += 1
            logger.warning("RAG Guardrail rejected sensitive file: %s", file_path)
            return False

        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                raw_content = f.read()
        except Exception:
            return False

        # Guardrail: Sanitize document content
        content, was_modified = sanitize_document_content(raw_content)
        if was_modified:
            self.sanitized_injections_count += 1
            logger.info("RAG Guardrail sanitized indirect prompt injection in file: %s", file_path)

        file_chunks_added = 0

        # Handle Markdown sections or general code files
        if file_path.endswith(".md"):
            # Split by markdown headers
            sections = re.split(r"(?=(?:^|\n)#{1,3}\s)", content)
            chunk_id = 0
            for sec in sections:
                if len(sec.strip()) > 30:
                    chunk = DocumentChunk(
                        source_path=file_path,
                        chunk_id=chunk_id,
                        content=sec.strip(),
                        title=Path(file_path).name,
                    )
                    self.chunks.append(chunk)
                    chunk_id += 1
                    file_chunks_added += 1
        else:
            # Fixed-window chunking
            lines = content.splitlines()
            line_chunk_size = 40
            line_overlap = 10
            step = max(1, line_chunk_size - line_overlap)
            chunk_id = 0
            for i in range(0, len(lines), step):
                chunk_lines = lines[i : i + line_chunk_size]
                chunk_text = "\n".join(chunk_lines)
                if len(chunk_text.strip()) > 20:
                    chunk = DocumentChunk(
                        source_path=file_path,
                        chunk_id=chunk_id,
                        content=chunk_text,
                        title=Path(file_path).name,
                    )
                    self.chunks.append(chunk)
                    chunk_id += 1
                    file_chunks_added += 1

        return file_chunks_added > 0

    def _recompute_bm25_stats(self):
        """Compute document frequencies and average document length for BM25 ranking."""
        self.doc_freqs = {}
        self.total_docs = len(self.chunks)
        if self.total_docs == 0:
            self.avg_doc_len = 0.0
            return

        total_tokens = 0
        for chunk in self.chunks:
            total_tokens += len(chunk.tokens)
            unique_tokens = set(chunk.tokens)
            for token in unique_tokens:
                self.doc_freqs[token] = self.doc_freqs.get(token, 0) + 1

        self.avg_doc_len = total_tokens / self.total_docs

    def _score_bm25(self, query_tokens: List[str], chunk: DocumentChunk, k1: float = 1.5, b: float = 0.75) -> float:
        """Calculate Okapi BM25 relevance score for a chunk given query tokens."""
        score = 0.0
        doc_len = len(chunk.tokens)
        if doc_len == 0 or self.total_docs == 0:
            return 0.0

        # Term frequencies in chunk
        tf_map: Dict[str, int] = {}
        for tok in chunk.tokens:
            tf_map[tok] = tf_map.get(tok, 0) + 1

        for q in query_tokens:
            if q not in tf_map:
                continue
            tf = tf_map[q]
            df = self.doc_freqs.get(q, 0)
            idf = math.log(1.0 + (self.total_docs - df + 0.5) / (df + 0.5))
            
            numerator = tf * (k1 + 1.0)
            denominator = tf + k1 * (1.0 - b + b * (doc_len / (self.avg_doc_len or 1.0)))
            score += idf * (numerator / denominator)

        return score

    def decompose_query(self, transcript: str) -> List[str]:
        """Decompose a free-form spoken transcript into focused technical search queries."""
        # Clean text
        clean_text = re.sub(r"[^\w\s\.\-]", " ", transcript)
        sentences = [s.strip() for s in re.split(r"[.\n]+", clean_text) if len(s.strip()) > 15]

        # Extract domain keywords
        keywords = re.findall(
            r"\b(?:api|database|auth|model|frontend|backend|framework|schema|workflow|test|deploy|docker|groq|whisper|llm|rag|ui|component|service|endpoint|token|state|react|python|fastapi|pyqt)\b",
            clean_text.lower(),
        )

        queries = []
        if keywords:
            queries.append(" ".join(list(set(keywords))))

        # Take up to 3 descriptive sentences
        for sentence in sentences[:3]:
            queries.append(sentence)

        if not queries:
            queries.append(transcript[:200])

        return queries

    def search(self, query: str, top_k: Optional[int] = None) -> List[Tuple[DocumentChunk, float]]:
        """Search indexed knowledge base for top matching chunks."""
        if not self.chunks:
            return []

        k = top_k or self.top_k
        query_tokens = DocumentChunk._tokenize(query)
        if not query_tokens:
            return []

        scored_chunks: List[Tuple[DocumentChunk, float]] = []
        for chunk in self.chunks:
            score = self._score_bm25(query_tokens, chunk)
            if score > 0.01:
                scored_chunks.append((chunk, score))

        scored_chunks.sort(key=lambda x: x[1], reverse=True)
        return scored_chunks[:k]

    def retrieve_grounded_context(self, transcript: str, top_k: Optional[int] = None) -> str:
        """Decomposes transcript, retrieves top matching context chunks, and formats them for prompt injection with guardrails."""
        if not self.chunks:
            return ""

        queries = self.decompose_query(transcript)
        seen_chunks = set()
        matched_results: List[Tuple[DocumentChunk, float]] = []

        for q in queries:
            results = self.search(q, top_k=top_k or self.top_k)
            for chunk, score in results:
                # Guardrail: Filter chunks below minimum relevance threshold
                if score < self.min_relevance_threshold:
                    continue
                identifier = f"{chunk.source_path}:{chunk.chunk_id}"
                if identifier not in seen_chunks:
                    seen_chunks.add(identifier)
                    matched_results.append((chunk, score))

        matched_results.sort(key=lambda x: x[1], reverse=True)
        top_matches = matched_results[: (top_k or self.top_k)]

        if not top_matches:
            return ""

        context_blocks = ["### Retrieved Project & Architecture Context (RAG):"]
        for chunk, score in top_matches:
            source_basename = Path(chunk.source_path).name
            clean_chunk, _ = sanitize_document_content(chunk.content)
            context_blocks.append(
                f"**[Source: {source_basename} (Section {chunk.chunk_id})]** (Relevance: {score:.2f})\n```\n{clean_chunk}\n```"
            )

        return "\n\n".join(context_blocks)

    def query(self, transcript: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """CouncilEngine compatible RAG interface.
        
        Returns a list of dictionaries with 'file', 'text', 'score', and 'chunk_id' keys.
        """
        if not self.chunks:
            return []

        search_results = self.search(transcript, top_k=top_k)
        if not search_results:
            # Fallback to query decomposition if direct search yielded no tokens
            decomposed = self.decompose_query(transcript)
            for d in decomposed:
                search_results = self.search(d, top_k=top_k)
                if search_results:
                    break

        output = []
        for chunk, score in search_results:
            if score >= self.min_relevance_threshold:
                clean_text, _ = sanitize_document_content(chunk.content)
                output.append({
                    "file": Path(chunk.source_path).name,
                    "text": clean_text,
                    "score": round(score, 3),
                    "chunk_id": chunk.chunk_id,
                    "title": chunk.title
                })
        return output

    def query_document(
        self,
        query: str,
        top_k: int = 3,
        model_router: Optional[Any] = None
    ) -> Dict[str, Any]:
        """Enterprise Document Query QA Engine with Zero-Hallucination Guardrails.
        
        Evaluates input query for prompt injections, retrieves matching chunks,
        verifies relevance against threshold, and synthesizes a grounded answer with exact citations.
        """
        # Guardrail 1: Check query for injection attempts
        clean_query, query_injected = sanitize_document_content(query)
        
        # Guardrail 2: Search indexed documents
        matches = self.search(clean_query, top_k=top_k)
        
        # Guardrail 3: Filter by relevance threshold to prevent hallucinated grounding
        grounded_matches = [(c, s) for c, s in matches if s >= self.min_relevance_threshold]
        is_grounded = len(grounded_matches) > 0

        citations = []
        context_snippets = []
        for chunk, score in grounded_matches:
            clean_text, _ = sanitize_document_content(chunk.content)
            citations.append({
                "file": Path(chunk.source_path).name,
                "chunk_id": chunk.chunk_id,
                "score": round(score, 3),
                "snippet": clean_text[:200] + ("..." if len(clean_text) > 200 else "")
            })
            context_snippets.append(f"[{Path(chunk.source_path).name} §{chunk.chunk_id}]: {clean_text}")

        context_block = "\n\n".join(context_snippets)

        # Synthesis
        answer = ""
        if not is_grounded:
            answer = (
                "Guardrail Notice: No sufficiently grounded context found in indexed documents "
                f"matching query '{clean_query}'. Refusing to hallucinate unverified specifications."
            )
        elif model_router and hasattr(model_router, "generate"):
            system_prompt = (
                "You are the Vo-Gen-Flow Document Intelligence Engine. "
                "Answer the user's question using ONLY the retrieved document snippets below. "
                "Cite your sources precisely using [Filename §ChunkID]. "
                "If the answer is not present in the context, explicitly state that it is not documented."
            )
            user_prompt = f"Retrieved Context:\n{context_block}\n\nUser Question:\n{clean_query}"
            res = model_router.generate("default", system_prompt, user_prompt)
            answer = res.get("content", "")
        else:
            # Extractive deterministic answer for air-gapped / offline mode
            top_chunk, top_score = grounded_matches[0]
            answer = (
                f"Grounded insight from {Path(top_chunk.source_path).name} (Section {top_chunk.chunk_id}, score {top_score:.2f}):\n\n"
                f"{top_chunk.content[:400]}..."
            )

        return {
            "query": clean_query,
            "answer": answer,
            "grounded": is_grounded,
            "citations": citations,
            "guardrail_telemetry": {
                "query_injection_neutralized": query_injected,
                "blocked_sensitive_files": self.blocked_sensitive_files,
                "sanitized_injections_in_db": self.sanitized_injections_count,
                "top_relevance_score": round(grounded_matches[0][1], 3) if grounded_matches else 0.0,
                "chunks_evaluated": len(self.chunks)
            }
        }

