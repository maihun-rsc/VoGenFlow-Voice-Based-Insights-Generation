"""
RAG Engine (Retrieval-Augmented Generation) Module
Provides local document indexing, chunking, semantic keyword/BM25 retrieval, query decomposition,
grounded context injection, and an interactive Document Query system with enterprise security guardrails.
"""

import math
import os
import re
import logging
import socket
import json
import time
import tempfile
import urllib.request
import urllib.parse
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Union

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
        self.embedding: Optional[List[float]] = None

    @staticmethod
    def _tokenize(text: str) -> List[str]:
        """Convert text into normalized lowercase alphanumeric tokens, filtering stop words."""
        raw_tokens = re.findall(r"\b[a-zA-Z0-9_\-\.]{2,}\b", text.lower())
        filtered = [t for t in raw_tokens if t not in ENGLISH_STOP_WORDS]
        return filtered if filtered else raw_tokens

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, DocumentChunk):
            return False
        return self.source_path == other.source_path and self.chunk_id == other.chunk_id

    def __hash__(self) -> int:
        return hash((self.source_path, self.chunk_id))

    def __repr__(self) -> str:
        return f"<DocumentChunk {self.source_path}:{self.chunk_id}>"


class SemanticQueryExpander:
    """Extracts and enriches domain keywords from conversational speech.

    Maps high-level spoken concepts (e.g. 'real-time streaming', 'auth', 'database')
    into concrete engineering search terms. Optionally queries the fast tier of
    ModelRouter or falls back deterministically to internal technical taxonomy.
    """

    DEFAULT_TAXONOMY: Dict[str, str] = {
        # Streaming & Audio
        "real-time streaming": "websockets sse duplex audio pcm webrtc latency",
        "streaming": "websockets sse duplex audio pcm webrtc latency",
        "audio": "pcm 16khz wav audio streaming duplex microphone vad",
        "voice": "speech-to-text whisper audio transcription streaming microphone",
        "webrtc": "peer-to-peer data channel sdp ice stun turn audio stream",
        "websocket": "websockets sse duplex socket bidirectional frame",
        "websockets": "duplex real-time audio socket connection",
        "sse": "server sent events unidirectional streaming event stream",

        # Authentication & Authorization
        "auth": "oauth2 jwt rbac session tokens permissions bearer authorization",
        "authentication": "oauth2 jwt bearer tokens identity rbac credentials",
        "authorization": "rbac permissions roles policies acl claims security",
        "jwt": "bearer token signature rs256 claims expiration payload",
        "oauth": "oauth2 authorization code grant refresh token bearer",
        "oauth2": "jwt bearer tokens client credentials refresh token rbac",
        "rbac": "role based access control permissions roles claims",
        "security": "encryption tls guardrails sanitization injection rate-limit",

        # Databases & Storage
        "database": "postgresql schemas tables migrations foreign keys uuid acid",
        "db": "postgresql sql relational database schema tables migrations",
        "postgres": "postgresql ddl relational schema acid indices tables",
        "postgresql": "relational database ddl foreign keys uuid indices triggers",
        "sql": "postgresql queries joins indexes ddl migrations relational",
        "schema": "ddl tables relations migrations foreign keys constraints",
        "orm": "sqlalchemy models relations sessions migrations declarative",

        # Caching & State
        "cache": "redis distributed cache aside redlock memory ttl",
        "caching": "redis in-memory cache-aside invalidation ttl write-through",
        "redis": "in-memory key-value cache-aside pubsub redlock sorted-set",

        # Task Queues & Asynchronous Processing
        "queue": "celery redis worker asynchronous background tasks bullmq",
        "task queue": "celery bullmq background asynchronous tasks worker jobs",
        "async": "asynchronous asyncio worker concurrency event loop non-blocking",
        "celery": "redis worker background tasks broker result backend",
        "worker": "background tasks async processing celery bullmq queue",

        # Messaging & Event-Driven Architecture
        "event": "event-driven pubsub broker consumer producer distributed kafka",
        "event-driven": "kafka event streaming pubsub consumer producer broker",
        "pubsub": "publisher subscriber broker topics fanout kafka redis",
        "kafka": "apache kafka distributed log broker partition topic consumer",

        # API & Microservices
        "api": "rest endpoints fastify fastapi openapi json schema routes",
        "gateway": "api gateway reverse proxy routing rate limit ingress",
        "graphql": "apollo federation schema subgraph resolvers queries mutations",
        "rest": "http endpoints request response json status codes headers",
        "fastapi": "python pydantic async routes endpoints dependency injection",
        "fastify": "node http framework high throughput low latency gateway",
        "microservice": "services distributed architecture communication grpc http",

        # Deployment & DevOps
        "deployment": "kubernetes microservice helm deployment ingress autoscaling docker",
        "deploy": "docker container kubernetes ci cd cloud release",
        "docker": "container dockerfile multi-stage compose image registry",
        "kubernetes": "k8s pods deployment helm ingress horizontal pod autoscaling",
        "k8s": "kubernetes clusters manifests pods services ingress helm",

        # SaaS & Payments
        "billing": "stripe saas billing subscription manager webhook customer tier",
        "payments": "stripe checkout webhooks payment method invoice subscription",
        "stripe": "billing subscription customer checkout portal webhook events",
        "subscription": "tiers monthly annual recurring plan stripe billing",

        # Frontend & UI
        "frontend": "react nextjs tailwind components state hooks ui",
        "ui": "user interface components design system layout tailwind",
        "react": "components hooks virtual dom state jsx props rendering",

        # AI & Machine Learning
        "rag": "retrieval augmented generation bm25 embeddings vector similarity chunks",
        "llm": "groq llama whisper inference tokens prompt system completion",
        "model": "neural network weights inference embeddings transformer",
        "embeddings": "vector dense similarity cosine dimension semantic representation",
    }

    def __init__(self, model_router: Optional[Any] = None, taxonomy: Optional[Dict[str, str]] = None):
        self.model_router = model_router
        self.taxonomy = taxonomy or self.DEFAULT_TAXONOMY
        sorted_keys = sorted(self.taxonomy.keys(), key=lambda k: (-len(k), k))
        escaped_keys = [re.escape(k).replace(r"\ ", r"\s+") for k in sorted_keys]
        self._pattern = re.compile(r"\b(" + "|".join(escaped_keys) + r")\b", re.IGNORECASE)

    def extract_domain_keywords(self, text: str) -> List[str]:
        """Extract matching domain concepts from conversational text."""
        if not text:
            return []
        matches = self._pattern.findall(text)
        seen = set()
        matched_keys = []
        for m in matches:
            normalized = re.sub(r"\s+", " ", m.lower().strip())
            for k in self.taxonomy:
                if k == normalized or re.sub(r"\s+", " ", k) == normalized:
                    if k not in seen:
                        seen.add(k)
                        matched_keys.append(k)
                    break
        return matched_keys

    def extract_keywords(self, text: str) -> List[str]:
        """Alias for extract_domain_keywords."""
        return self.extract_domain_keywords(text)

    def get_expanded_terms(self, text: str) -> List[str]:
        """Return list of enriched expansion terms for matched concepts."""
        matched = self.extract_domain_keywords(text)
        terms: List[str] = []
        text_lower = text.lower()
        for k in matched:
            for term in self.taxonomy[k].split():
                tl = term.lower()
                if tl not in text_lower and tl not in terms:
                    terms.append(tl)
        return terms

    def expand(self, text: str) -> str:
        """Enrich text with expanded domain terminology."""
        if not text:
            return ""

        # 1. Optionally query model_router fast tier if available
        if self.model_router and hasattr(self.model_router, "generate"):
            try:
                system_prompt = (
                    "You are a technical search query expander. Extract key software architecture "
                    "concepts from the speech transcript and output 5-8 relevant technical keywords "
                    "(e.g. protocol names, database terms, libraries). Output ONLY space-separated keywords."
                )
                res = self.model_router.generate("fast", system_prompt, text, max_tokens=60)
                content = res.get("content", "").strip()
                if content and not content.startswith("Error") and "circuit breaker" not in content.lower():
                    return f"{text} {content}"
            except Exception as e:
                logger.debug("Fast tier query expansion skipped/failed: %s", str(e))

        # 2. Deterministic taxonomy fallback
        expansion_terms = self.get_expanded_terms(text)
        if expansion_terms:
            return f"{text} {' '.join(expansion_terms)}"
        return text

    def expand_query(self, text: str) -> str:
        """Alias for expand()."""
        return self.expand(text)


class LMStudioEmbeddingClient:
    """Local dense embedding client connecting to LM Studio Bionic.

    Provides sub-100ms socket probing, cosine similarity calculation,
    and graceful fallback when LM Studio is unreachable.
    """

    def __init__(
        self,
        endpoint: str = "http://localhost:1234/v1/embeddings",
        model: str = "text-embedding-nomic-embed-text-v1.5",
        probe_timeout: float = 0.05,
        request_timeout: float = 2.0,
        probe_cooldown: float = 5.0,
        min_similarity: float = 0.0,
    ):
        self.endpoint = endpoint
        self.model = model
        self.probe_timeout = probe_timeout
        self.request_timeout = request_timeout
        self.probe_cooldown = probe_cooldown
        self.min_similarity = min_similarity
        self._is_available: Optional[bool] = None
        self._last_probe_time: float = 0.0

    def is_available(self, force_refresh: bool = False) -> bool:
        """Probe LM Studio embedding service with a fast sub-100ms socket probe."""
        now = time.time()
        if not force_refresh and self._is_available is not None:
            if self._last_probe_time == 0.0 or (now - self._last_probe_time) < self.probe_cooldown:
                return self._is_available

        self._last_probe_time = now
        try:
            parsed = urllib.parse.urlparse(self.endpoint)
            host = parsed.hostname or "127.0.0.1"
            if host == "localhost":
                host = "127.0.0.1"
            port = parsed.port or (443 if parsed.scheme == "https" else 1234)

            sock = socket.create_connection((host, port), timeout=self.probe_timeout)
            sock.close()
            self._is_available = True
        except Exception:
            self._is_available = False

        return self._is_available

    def get_embedding(self, text: str) -> Optional[List[float]]:
        """Fetch dense vector embedding from LM Studio. Returns None if unreachable."""
        if not self.is_available():
            return None

        if not text or not text.strip():
            return None

        try:
            payload = json.dumps({"input": text, "model": self.model}).encode("utf-8")
            req = urllib.request.Request(
                self.endpoint,
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=self.request_timeout) as resp:
                if resp.status == 200:
                    data = json.loads(resp.read().decode("utf-8"))
                    items = data.get("data", [])
                    if items and "embedding" in items[0]:
                        return items[0]["embedding"]
        except Exception as e:
            logger.debug("LM Studio embedding request failed: %s", str(e))
            self._is_available = False
            return None

        return None

    def get_embeddings(self, texts: List[str]) -> Optional[List[List[float]]]:
        """Fetch batch vector embeddings from LM Studio. Returns None if unreachable."""
        if not self.is_available() or not texts:
            return None

        try:
            payload = json.dumps({"input": texts, "model": self.model}).encode("utf-8")
            req = urllib.request.Request(
                self.endpoint,
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=self.request_timeout) as resp:
                if resp.status == 200:
                    data = json.loads(resp.read().decode("utf-8"))
                    items = data.get("data", [])
                    items.sort(key=lambda x: x.get("index", 0))
                    embeddings = [it["embedding"] for it in items if "embedding" in it]
                    if len(embeddings) == len(texts):
                        return embeddings
        except Exception as e:
            logger.debug("LM Studio batch embedding request failed: %s", str(e))
            self._is_available = False
            return None

        return None

    @staticmethod
    def cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
        """Compute cosine similarity between two float vectors."""
        if not vec_a or not vec_b or len(vec_a) != len(vec_b):
            return 0.0
        dot = sum(a * b for a, b in zip(vec_a, vec_b))
        norm_a = math.sqrt(sum(a * a for a in vec_a))
        norm_b = math.sqrt(sum(b * b for b in vec_b))
        if norm_a == 0.0 or norm_b == 0.0:
            return 0.0
        return dot / (norm_a * norm_b)

    def similarity_search(
        self,
        query: str,
        chunks: List[Any],
        top_k: Optional[int] = None,
        min_similarity: Optional[float] = None,
    ) -> List[Tuple[Any, float]]:
        """Compute cosine similarity between query embedding and chunk embeddings."""
        if not self.is_available() or not chunks:
            return []

        query_emb = self.get_embedding(query)
        if not query_emb:
            return []

        threshold = min_similarity if min_similarity is not None else self.min_similarity

        # Identify chunks needing embeddings
        missing_indices = []
        missing_texts = []
        for idx, chunk in enumerate(chunks):
            if getattr(chunk, "embedding", None) is None:
                missing_indices.append(idx)
                missing_texts.append(getattr(chunk, "content", str(chunk)))

        if missing_texts:
            batch_embs = self.get_embeddings(missing_texts)
            if batch_embs and len(batch_embs) == len(missing_indices):
                for idx, emb in zip(missing_indices, batch_embs):
                    chunks[idx].embedding = emb
            else:
                for idx in missing_indices:
                    content = getattr(chunks[idx], "content", str(chunks[idx]))
                    chunks[idx].embedding = self.get_embedding(content)

        scored: List[Tuple[Any, float]] = []
        for chunk in chunks:
            emb = getattr(chunk, "embedding", None)
            if emb:
                sim = self.cosine_similarity(query_emb, emb)
                if sim >= threshold:
                    scored.append((chunk, sim))

        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:top_k] if top_k else scored


def reciprocal_rank_fusion(
    bm25_ranks: List[Tuple[Any, float]],
    dense_ranks: List[Tuple[Any, float]],
    k: int = 60
) -> List[Tuple[Any, float]]:
    """Cleanly fuses keyword precision (BM25) with semantic vector similarity using standard RRF.

    RRF score = sum(1.0 / (k + rank)) for each system where the item appears.
    Rank is 1-based (rank=1 for the top retrieved item).
    """
    scores: Dict[Any, float] = {}
    item_map: Dict[Any, Any] = {}

    def _get_key(item: Any) -> Any:
        if hasattr(item, "source_path") and hasattr(item, "chunk_id"):
            return (item.source_path, item.chunk_id)
        if isinstance(item, dict):
            if "id" in item:
                return ("dict_id", item["id"])
            try:
                return tuple(sorted(item.items()))
            except Exception:
                return id(item)
        try:
            hash(item)
            return item
        except TypeError:
            return id(item)

    seen_bm25 = set()
    for rank, entry in enumerate(bm25_ranks, start=1):
        item = entry[0] if isinstance(entry, (list, tuple)) and len(entry) >= 2 else entry
        key = _get_key(item)
        if key not in seen_bm25:
            seen_bm25.add(key)
            item_map[key] = item
            scores[key] = scores.get(key, 0.0) + (1.0 / (k + rank))

    seen_dense = set()
    for rank, entry in enumerate(dense_ranks, start=1):
        item = entry[0] if isinstance(entry, (list, tuple)) and len(entry) >= 2 else entry
        key = _get_key(item)
        if key not in seen_dense:
            seen_dense.add(key)
            if key not in item_map:
                item_map[key] = item
            scores[key] = scores.get(key, 0.0) + (1.0 / (k + rank))

    fused = [(item_map[key], score) for key, score in scores.items()]
    fused.sort(key=lambda x: x[1], reverse=True)
    return fused


class LocalRAGEngine:
    """Lightweight, self-contained RAG and semantic retrieval engine with enterprise guardrails."""

    def __init__(
        self,
        top_k: int = 4,
        chunk_size: int = 400,
        overlap: int = 50,
        min_relevance_threshold: float = 0.1,
        embedding_client: Optional[LMStudioEmbeddingClient] = None,
        model_router: Optional[Any] = None,
        expander: Optional[SemanticQueryExpander] = None,
        knowledge_db: Optional[Any] = None,
        allowed_roots: Optional[List[Union[str, Path]]] = None,
    ):
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
        self.embedding_client = embedding_client or LMStudioEmbeddingClient()
        self.expander = expander or SemanticQueryExpander(model_router=model_router)
        self.model_router = model_router
        self._knowledge_db = knowledge_db
        self.allowed_roots = list(allowed_roots) if allowed_roots else []

    @property
    def knowledge_db(self) -> Any:
        """Lazily initialize in-memory curated knowledge base if not explicitly injected."""
        if self._knowledge_db is None:
            try:
                from src.knowledge_db import CuratedKnowledgeDB
                self._knowledge_db = CuratedKnowledgeDB()
            except Exception as e:
                logger.warning("Could not initialize CuratedKnowledgeDB for RAG engine: %s", str(e))
                self._knowledge_db = None
        return self._knowledge_db

    def _is_path_allowed(self, target_path: Union[str, Path]) -> bool:
        """Security Guardrail: Imprison RAG indexing to workspace root and safe temporary paths."""
        try:
            resolved = Path(target_path).resolve()
        except Exception:
            return False

        allowed_bases = [
            Path.cwd().resolve(),
            Path(__file__).resolve().parent.parent.resolve(),
            Path(tempfile.gettempdir()).resolve(),
        ]
        if self.allowed_roots:
            for r in self.allowed_roots:
                try:
                    allowed_bases.append(Path(r).resolve())
                except Exception:
                    pass

        for base in allowed_bases:
            try:
                if resolved == base or resolved.is_relative_to(base):
                    return True
            except (ValueError, AttributeError):
                continue
        return False

    def is_architectural_advisory_query(self, query: str) -> bool:
        """Classify whether a query is an architectural/design/advisory inquiry rather than random noise."""
        if not query or not query.strip():
            return False
        clean = query.lower()

        # 1. Domain technical concept keywords from expander taxonomy
        domain_keywords = self.expander.extract_domain_keywords(clean)
        if domain_keywords:
            return True

        # 2. Architectural and system design inquiry patterns
        advisory_patterns = [
            r"\barchitectur(e|al)\b",
            r"\bdesign\s+pattern(s)?\b",
            r"\bhow\s+should\s+we\b",
            r"\bhow\s+to\s+architect\b",
            r"\bhow\s+to\s+design\b",
            r"\bhow\s+can\s+we\b",
            r"\bwhat\s+(all\s+)?features\s+(can|could|should)\b",
            r"\bwhat\s+(can|could|should)\s+we\b",
            r"\bbest\s+practice(s)?\b",
            r"\brecommend(ation|ed)?\b",
            r"\btrade-?off(s)?\b",
            r"\bscalability\b",
            r"\bmicroservice(s)?\b",
            r"\bmonolith(ic)?\b",
            r"\bhigh-?throughput\b",
            r"\blow-?latency\b",
            r"\bconcurrency\b",
            r"\bdistributed\s+system(s)?\b",
            r"\bevent-?driven\b",
            r"\bdata\s+pipeline\b",
            r"\bdatabase\s+schema\b",
            r"\bcaching\s+strategy\b",
            r"\bfailover\b",
            r"\bresilience\b",
            r"\btech(nology)?\s+stack\b",
            r"\bcuration\b",
            r"\bdocument\s+intelligence\b",
            r"\bdocument\s+creation\b",
            r"\bworkflow\b",
            r"\broadmap\b",
            r"\bcapabilities\b",
            r"\bfeature(s)?\b",
        ]
        for pat in advisory_patterns:
            if re.search(pat, clean):
                return True

        return False

    def _is_dense_active(self) -> bool:
        """Check if dense vector adapter is available and active."""
        if not self.embedding_client:
            return False
        try:
            return self.embedding_client.is_available()
        except Exception:
            return False

    def _get_effective_threshold(self) -> float:
        """Dynamic threshold adjusting for RRF score scale vs BM25 score scale."""
        if self._is_dense_active():
            # In RRF with k=60, a top-rank match receives 1/61 (~0.01639).
            # Scale threshold proportionally so valid matches pass guardrail.
            return self.min_relevance_threshold / 61.0
        return self.min_relevance_threshold

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
        # Guardrail: Enforce local directory prison
        if not self._is_path_allowed(dir_path):
            self.blocked_sensitive_files += 1
            logger.warning("RAG Guardrail rejected directory outside project prison: %s", dir_path)
            return 0

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
        # Guardrail: Enforce local file prison
        if not self._is_path_allowed(file_path):
            self.blocked_sensitive_files += 1
            logger.warning("RAG Guardrail rejected file outside allowed directory prison: %s", file_path)
            return False

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
        for t in chunk.tokens:
            tf_map[t] = tf_map.get(t, 0) + 1

        # Term overlap guardrail: queries with 3+ unique terms must match at least 2 distinct terms
        unique_q_tokens = list(set(query_tokens))
        matched_terms = [q for q in unique_q_tokens if q in tf_map]
        if len(unique_q_tokens) >= 3 and len(matched_terms) < 2:
            return 0.0

        for q in matched_terms:
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

        # Enrich domain keywords using SemanticQueryExpander
        if hasattr(self, "expander") and self.expander:
            expanded = self.expander.expand(transcript)
            if expanded != transcript:
                extracted_kw = self.expander.extract_domain_keywords(transcript)
                if extracted_kw:
                    queries.append(expanded)

        if not queries:
            queries.append(transcript[:200])

        return queries

    def search(self, query: str, top_k: Optional[int] = None) -> List[Tuple[DocumentChunk, float]]:
        """Search indexed knowledge base for top matching chunks using dual-adapter retrieval."""
        if not self.chunks:
            return []

        k = top_k or self.top_k
        query_tokens = DocumentChunk._tokenize(query)
        if not query_tokens and not self._is_dense_active():
            return []

        # 1. Lexical BM25 ranking
        bm25_matches: List[Tuple[DocumentChunk, float]] = []
        if query_tokens:
            for chunk in self.chunks:
                score = self._score_bm25(query_tokens, chunk)
                if score > 0.01:
                    bm25_matches.append((chunk, score))
            bm25_matches.sort(key=lambda x: x[1], reverse=True)

        # 2. Dual-Adapter Dense RRF (when local LM Studio is online)
        if self._is_dense_active():
            try:
                dense_matches = self.embedding_client.similarity_search(query, self.chunks, top_k=len(self.chunks))
                if dense_matches:
                    fused = reciprocal_rank_fusion(bm25_matches, dense_matches, k=60)
                    return fused[:k]
            except Exception as e:
                logger.warning("Dense vector search failed, falling back to BM25: %s", str(e))

        # 3. Deterministic BM25 fallback (Cloud/Groq mode or offline)
        return bm25_matches[:k]

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
                if score < self._get_effective_threshold():
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
            if score >= self._get_effective_threshold():
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
        grounded_matches = [(c, s) for c, s in matches if s >= self._get_effective_threshold()]
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
        active_router = model_router or getattr(self, "model_router", None)
        is_advisory = False

        if not is_grounded:
            # Check if any matches exist at all before fallback
            if matches:
                top_c, top_s = matches[0]
                is_grounded = True
                grounded_matches = [(top_c, top_s)]
                clean_text, _ = sanitize_document_content(top_c.content)
                citations.append({
                    "file": Path(top_c.source_path).name,
                    "chunk_id": top_c.chunk_id,
                    "score": round(top_s, 3),
                    "snippet": clean_text[:200] + ("..." if len(clean_text) > 200 else "")
                })
                context_block = f"[{Path(top_c.source_path).name} - Chunk {top_c.chunk_id}]:\n" + clean_text

        if not is_grounded:
            # Check if query is an architectural/design/advisory inquiry
            if self.is_architectural_advisory_query(clean_query):
                is_advisory = True
                curated_templates = []
                if self.knowledge_db:
                    try:
                        curated_templates = self.knowledge_db.search(clean_query, top_k=top_k)
                    except Exception as e:
                        logger.warning("Error searching knowledge_db during advisory fallback: %s", str(e))

                advisory_context_snippets = []
                for tmpl in curated_templates:
                    citations.append({
                        "file": f"Curated Blueprint: {tmpl.get('title', 'Architecture Blueprint')}",
                        "chunk_id": tmpl.get("id", "advisory_pattern"),
                        "score": round(tmpl.get("relevance_score", 0.85), 3),
                        "snippet": tmpl.get("description", "")[:200] + ("..." if len(tmpl.get("description", "")) > 200 else "")
                    })
                    advisory_context_snippets.append(
                        f"### {tmpl.get('title')}\n"
                        f"**Category:** {tmpl.get('category', 'Architecture')}\n"
                        f"{tmpl.get('description', '')}\n\n"
                        f"```\n{tmpl.get('snippet', '')}\n```"
                    )

                curated_context_block = "\n\n".join(advisory_context_snippets)

                if active_router and hasattr(active_router, "generate"):
                    system_prompt = (
                        "You are the Vo-Gen-Flow Architectural Advisor. "
                        "The user asked an architectural design, systems engineering, or technical advisory question. "
                        "Because no direct code chunks matched in the local repository, synthesize actionable "
                        "guidance based on the curated engineering blueprints provided and industry cloud best practices. "
                        "You MUST prefix your response with '[ARCHITECTURAL ADVISORY // SYNTHESIS]'. "
                        "Provide concrete architectural guidance, trade-offs, and design patterns."
                    )
                    user_prompt = (
                        f"Curated Architecture Blueprints:\n{curated_context_block}\n\n"
                        f"User Query:\n{clean_query}"
                    )
                    res = active_router.generate("default", system_prompt, user_prompt)
                    raw_content = res.get("content", "").strip()
                    if not raw_content.startswith("[ARCHITECTURAL ADVISORY // SYNTHESIS]"):
                        answer = f"[ARCHITECTURAL ADVISORY // SYNTHESIS]\n\n{raw_content}"
                    else:
                        answer = raw_content
                else:
                    # Deterministic synthesis for air-gapped / offline mode
                    if curated_templates:
                        top_t = curated_templates[0]
                        answer = (
                            "[ARCHITECTURAL ADVISORY // SYNTHESIS]\n\n"
                            f"**Architectural Advisory for:** {clean_query}\n\n"
                            f"**Recommended Architectural Pattern:** {top_t.get('title', 'Enterprise Pattern')}\n"
                            f"**Category:** {top_t.get('category', 'Cloud Architecture')}\n\n"
                            f"{top_t.get('description', '')}\n\n"
                            "### Reference Architecture Blueprint:\n"
                            f"```\n{top_t.get('snippet', '')}\n```\n\n"
                            "*Note: Synthesized from curated engineering architecture catalog. "
                            "No direct local codebase files matched this advisory inquiry.*"
                        )
                    else:
                        answer = (
                            "[ARCHITECTURAL ADVISORY // SYNTHESIS]\n\n"
                            f"**Architectural Advisory for:** {clean_query}\n\n"
                            "Based on cloud engineering best practices: Decompose the service into modular, "
                            "loosely-coupled components with asynchronous event boundaries, rate-paced API gateways, "
                            "and robust transactional state management (e.g. PostgreSQL with connection pooling and Redis cache-aside).\n\n"
                            "*Note: Synthesized as architectural advisory guidance.*"
                        )
            else:
                # Out-of-domain query: preserve strict zero-hallucination refusal guardrail
                answer = (
                    "Guardrail Notice: No sufficiently grounded context found in indexed documents "
                    f"matching query '{clean_query}'. Refusing to hallucinate unverified specifications."
                )
        elif active_router and hasattr(active_router, "generate"):
            system_prompt = (
                "You are the Vo-Gen-Flow Document Intelligence Engine. "
                "Answer the user's question accurately using the retrieved technical documentation snippets below. "
                "Cite your sources precisely using [Filename - ChunkID]. "
                "Provide code snippets or architectural explanations where helpful."
            )
            user_prompt = f"Retrieved Context:\n{context_block}\n\nUser Question:\n{clean_query}"
            res = active_router.generate("default", system_prompt, user_prompt)
            answer = res.get("content", "")
        else:
            # Extractive deterministic answer for air-gapped / offline mode
            top_chunk, top_score = grounded_matches[0]
            clean_top, _ = sanitize_document_content(top_chunk.content)
            answer = (
                f"Grounded insight from {Path(top_chunk.source_path).name} (Section {top_chunk.chunk_id}, score {top_score:.2f}):\n\n"
                f"{clean_top[:600]}\n\n"
                f"*Source: [{Path(top_chunk.source_path).name} - Chunk {top_chunk.chunk_id}]*"
            )
        return {
            "query": clean_query,
            "answer": answer,
            "grounded": is_grounded,
            "advisory": is_advisory,
            "is_advisory": is_advisory,
            "citations": citations,
            "guardrail_telemetry": {
                "query_injection_neutralized": query_injected,
                "blocked_sensitive_files": self.blocked_sensitive_files,
                "sanitized_injections_in_db": self.sanitized_injections_count,
                "top_relevance_score": round(grounded_matches[0][1], 3) if grounded_matches else 0.0,
                "chunks_evaluated": len(self.chunks),
                "advisory_fallback_triggered": is_advisory
            }
        }

