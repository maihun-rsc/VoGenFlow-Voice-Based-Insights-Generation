"""
src/db/sqlite_store.py
Production-grade SQLite WAL-mode persistent storage adapter for VoGenFlow.

Implements high-performance, concurrent, ACID-compliant storage for:
- Projects
- Sessions & Session metadata
- Multi-version Generated Artifacts (PRD, Architecture, Flow, Tasks, Design)
- Canonical ProjectIR JSON specifications
- Embedded RAG Chunks and Citations
"""

import os
import json
import time
import uuid
import sqlite3
import threading
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Union, Tuple, Iterator

from src.config import Config

logger = logging.getLogger("vogenflow.db")


class ArtifactCollection(list):
    """
    Dual-access artifact collection.
    Behaves as a list of artifact record dicts, while also providing dictionary-style
    lookup by doc_type (e.g. artifacts["PRD.md"]).
    """

    def __init__(self, records: Optional[List[Dict[str, Any]]] = None):
        super().__init__(records or [])
        self._map: Dict[str, str] = {}
        for r in self:
            if isinstance(r, dict) and "doc_type" in r and "content" in r:
                self._map[r["doc_type"]] = r["content"]

    def __getitem__(self, item: Union[int, slice, str]) -> Any:
        if isinstance(item, str):
            if item in self._map:
                return self._map[item]
            raise KeyError(f"Artifact doc_type '{item}' not found in collection.")
        return super().__getitem__(item)

    def __contains__(self, item: object) -> bool:
        if isinstance(item, str):
            return item in self._map
        return super().__contains__(item)

    def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Fetch artifact content by doc_type or return default."""
        return self._map.get(key, default)

    def to_dict(self) -> Dict[str, str]:
        """Return doc_type -> content mapping."""
        return dict(self._map)


class ProjectIRRecord(dict):
    """
    ProjectIR record dictionary wrapper.
    Exposes canonical IR properties and provides `.to_model()` helper.
    """

    def __init__(
        self,
        data: Dict[str, Any],
        schema_version: str = "1.0.0",
        ir_json: str = "",
        session_id: str = "",
        updated_at: float = 0.0,
    ):
        super().__init__(data)
        self.schema_version = schema_version
        self.ir_json = ir_json
        self.session_id = session_id
        self.updated_at = updated_at
        # Ensure schema_version is present in dict view
        if "schema_version" not in self:
            self["schema_version"] = schema_version

    def to_model(self) -> Any:
        """Attempt to validate and return as Pydantic ProjectIR instance."""
        try:
            from src.models.project_ir import ProjectIR
            return ProjectIR.model_validate(self)
        except Exception as e:
            logger.warning("Could not convert ProjectIRRecord to ProjectIR model: %s", e)
            return None


class SQLiteStore:
    """
    Production-grade SQLite WAL-mode persistent storage adapter.
    Enforces WAL journaling, NORMAL synchronous mode, and foreign keys.
    Thread-safe with thread-local connections and fine-grained write synchronization.
    """

    SCHEMA_DDL = """
    CREATE TABLE IF NOT EXISTS projects (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        description TEXT,
        created_at REAL NOT NULL,
        updated_at REAL NOT NULL
    );

    CREATE TABLE IF NOT EXISTS sessions (
        id TEXT PRIMARY KEY,
        project_id TEXT,
        status TEXT NOT NULL DEFAULT 'active',
        created_at REAL NOT NULL,
        updated_at REAL NOT NULL,
        metadata_json TEXT,
        FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE SET NULL
    );

    CREATE TABLE IF NOT EXISTS artifacts (
        id TEXT PRIMARY KEY,
        session_id TEXT NOT NULL,
        doc_type TEXT NOT NULL,
        content TEXT NOT NULL,
        version INTEGER NOT NULL DEFAULT 1,
        created_at REAL NOT NULL,
        FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS project_ir (
        session_id TEXT PRIMARY KEY,
        schema_version TEXT NOT NULL DEFAULT '1.0.0',
        ir_json TEXT NOT NULL,
        updated_at REAL NOT NULL,
        FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS rag_chunks (
        id TEXT PRIMARY KEY,
        session_id TEXT,
        content TEXT NOT NULL,
        source TEXT,
        metadata_json TEXT,
        created_at REAL NOT NULL,
        FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE SET NULL
    );

    CREATE INDEX IF NOT EXISTS idx_sessions_project_id ON sessions(project_id);
    CREATE INDEX IF NOT EXISTS idx_sessions_created_at ON sessions(created_at DESC);
    CREATE INDEX IF NOT EXISTS idx_artifacts_session_id ON artifacts(session_id);
    CREATE INDEX IF NOT EXISTS idx_artifacts_doc_type ON artifacts(session_id, doc_type);
    CREATE INDEX IF NOT EXISTS idx_artifacts_lookup ON artifacts(session_id, doc_type, version);
    CREATE INDEX IF NOT EXISTS idx_rag_chunks_session_id ON rag_chunks(session_id);
    CREATE INDEX IF NOT EXISTS idx_rag_chunks_source ON rag_chunks(source);
    """

    def __init__(
        self,
        db_path: Optional[Union[str, Path]] = None,
        timeout: float = 30.0,
        auto_init: bool = True,
    ):
        """
        Initialize SQLiteStore.

        Args:
            db_path: Path to SQLite database file or ':memory:'.
                     Defaults to Config.OUTPUT_DIR / 'vogenflow.db'.
            timeout: Busy timeout in seconds for lock contention.
            auto_init: Whether to execute table creation on initialization.
        """
        if db_path is None:
            db_path = os.getenv("VOGENFLOW_DB_PATH") or (Config.OUTPUT_DIR / "vogenflow.db")

        self.db_path = str(db_path)
        self.timeout = timeout
        self._is_memory = (self.db_path == ":memory:")
        self._lock = threading.RLock()
        self._local = threading.local()
        self._shared_memory_conn: Optional[sqlite3.Connection] = None

        if self._is_memory:
            # Maintain a single shared in-memory connection across threads
            self._shared_memory_conn = self._create_raw_connection()

        if auto_init:
            self._init_db()

    def _create_raw_connection(self) -> sqlite3.Connection:
        """Create and configure a single SQLite connection with WAL pragmas."""
        if not self._is_memory:
            Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

        conn = sqlite3.connect(
            self.db_path,
            timeout=self.timeout,
            check_same_thread=False,
            isolation_level=None  # autocommit mode; we manage explicit transactions
        )
        conn.row_factory = sqlite3.Row

        # Pragmas
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.execute(f"PRAGMA busy_timeout = {int(self.timeout * 1000)};")
        conn.execute("PRAGMA synchronous = NORMAL;")

        # Enable WAL journal mode for non-memory databases
        if not self._is_memory:
            try:
                cur = conn.execute("PRAGMA journal_mode = WAL;")
                mode = cur.fetchone()
                logger.debug("SQLite journal_mode set to: %s", mode[0] if mode else "unknown")
            except Exception as e:
                logger.warning("Could not set WAL journal_mode: %s", e)

        return conn

    def get_connection(self) -> sqlite3.Connection:
        """Retrieve thread-local or shared in-memory SQLite connection."""
        if self._is_memory:
            return self._shared_memory_conn

        conn = getattr(self._local, "conn", None)
        if conn is None:
            conn = self._create_raw_connection()
            self._local.conn = conn
        return conn

    def _init_db(self):
        """Execute DDL statements to create tables and indices."""
        with self._lock:
            conn = self.get_connection()
            conn.executescript(self.SCHEMA_DDL)

    def get_journal_mode(self) -> str:
        """Return the current journal mode."""
        conn = self.get_connection()
        cur = conn.execute("PRAGMA journal_mode;")
        row = cur.fetchone()
        return str(row[0]).upper() if row else "UNKNOWN"

    def is_wal_mode(self) -> bool:
        """Check if WAL mode is active (or MEMORY for :memory: databases)."""
        mode = self.get_journal_mode()
        return mode in ("WAL", "MEMORY")

    def close(self):
        """Close open database connections."""
        with self._lock:
            if self._shared_memory_conn:
                try:
                    self._shared_memory_conn.close()
                except Exception:
                    pass
                self._shared_memory_conn = None

            conn = getattr(self._local, "conn", None)
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass
                self._local.conn = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def clear_all(self):
        """Truncate all tables for testing or resetting environment."""
        with self._lock:
            conn = self.get_connection()
            conn.execute("BEGIN IMMEDIATE")
            try:
                conn.execute("DELETE FROM rag_chunks")
                conn.execute("DELETE FROM project_ir")
                conn.execute("DELETE FROM artifacts")
                conn.execute("DELETE FROM sessions")
                conn.execute("DELETE FROM projects")
                conn.execute("COMMIT")
            except Exception:
                conn.execute("ROLLBACK")
                raise

    def get_stats(self) -> Dict[str, int]:
        """Return total row counts across all managed tables."""
        conn = self.get_connection()
        counts = {}
        for tbl in ("projects", "sessions", "artifacts", "project_ir", "rag_chunks"):
            cur = conn.execute(f"SELECT COUNT(*) FROM {tbl}")
            counts[tbl] = cur.fetchone()[0]
        return counts

    # =========================================================================
    # PROJECTS CRUD
    # =========================================================================

    def save_project(
        self,
        id: str,
        name: str,
        description: Optional[str] = None,
        created_at: Optional[float] = None,
        updated_at: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Create or update a project record."""
        now = time.time()
        c_at = created_at if created_at is not None else now
        u_at = updated_at if updated_at is not None else now

        with self._lock:
            conn = self.get_connection()
            conn.execute("BEGIN IMMEDIATE")
            try:
                conn.execute(
                    """
                    INSERT INTO projects (id, name, description, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?)
                    ON CONFLICT(id) DO UPDATE SET
                        name = excluded.name,
                        description = COALESCE(excluded.description, projects.description),
                        updated_at = excluded.updated_at
                    """,
                    (id, name, description, c_at, u_at),
                )
                conn.execute("COMMIT")
            except Exception:
                conn.execute("ROLLBACK")
                raise

        return self.get_project(id) or {
            "id": id,
            "name": name,
            "description": description,
            "created_at": c_at,
            "updated_at": u_at,
        }

    def get_project(self, project_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a project by ID."""
        conn = self.get_connection()
        cur = conn.execute("SELECT id, name, description, created_at, updated_at FROM projects WHERE id = ?", (project_id,))
        row = cur.fetchone()
        if not row:
            return None
        return dict(row)

    def list_projects(self, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        """List projects ordered by created_at DESC."""
        conn = self.get_connection()
        cur = conn.execute(
            "SELECT id, name, description, created_at, updated_at FROM projects ORDER BY created_at DESC LIMIT ? OFFSET ?",
            (limit, offset),
        )
        return [dict(row) for row in cur.fetchall()]

    def delete_project(self, project_id: str) -> bool:
        """Delete a project by ID. Foreign keys set session.project_id to NULL."""
        with self._lock:
            conn = self.get_connection()
            conn.execute("BEGIN IMMEDIATE")
            try:
                cur = conn.execute("DELETE FROM projects WHERE id = ?", (project_id,))
                deleted = cur.rowcount > 0
                conn.execute("COMMIT")
                return deleted
            except Exception:
                conn.execute("ROLLBACK")
                raise

    # =========================================================================
    # SESSIONS CRUD
    # =========================================================================

    def save_session(
        self,
        session_id: Union[str, Dict[str, Any]],
        project_id: Optional[str] = None,
        status: str = "active",
        metadata: Optional[Dict[str, Any]] = None,
        artifacts: Optional[Union[Dict[str, str], List[Dict[str, Any]]]] = None,
        project_ir: Optional[Any] = None,
        created_at: Optional[float] = None,
        updated_at: Optional[float] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """
        Create or update a session record, optionally saving artifacts and ProjectIR in one atomic flow.

        Supports both positional/keyword arguments and passing a full session dictionary.
        """
        # Handle dict input
        if isinstance(session_id, dict):
            data = session_id
            sid = str(data.get("session_id") or data.get("id"))
            p_id = data.get("project_id", project_id)
            st = data.get("status", status)
            c_at = data.get("created_at", created_at)
            u_at = data.get("updated_at", updated_at)
            arts = data.get("artifacts", artifacts)
            p_ir = data.get("project_ir", project_ir)
            # Gather metadata from dict: merge non-reserved top-level extra keys first,
            # then overlay explicit metadata dict so both are preserved and metadata takes precedence.
            meta = {
                k: v for k, v in data.items()
                if k not in (
                    "session_id", "id", "project_id", "status", "artifacts",
                    "artifact_records", "project_ir", "created_at", "updated_at", "metadata"
                )
            }
            raw_meta = data.get("metadata")
            if isinstance(raw_meta, dict):
                meta.update(raw_meta)
        else:
            sid = str(session_id)
            p_id = project_id
            st = status
            c_at = created_at
            u_at = updated_at
            arts = artifacts
            p_ir = project_ir
            meta = dict(metadata) if isinstance(metadata, dict) else {}
            if kwargs:
                meta.update(kwargs)

        now = time.time()
        final_created = c_at if c_at is not None else now
        final_updated = u_at if u_at is not None else now
        meta_json = json.dumps(meta) if meta else "{}"

        with self._lock:
            conn = self.get_connection()
            conn.execute("BEGIN IMMEDIATE")
            try:
                # If project_id provided, ensure parent project exists to prevent FK violation
                if p_id:
                    conn.execute(
                        """
                        INSERT OR IGNORE INTO projects (id, name, description, created_at, updated_at)
                        VALUES (?, ?, ?, ?, ?)
                        """,
                        (p_id, f"Project {p_id}", "Auto-generated project record", now, now),
                    )

                conn.execute(
                    """
                    INSERT INTO sessions (id, project_id, status, created_at, updated_at, metadata_json)
                    VALUES (?, ?, ?, ?, ?, ?)
                    ON CONFLICT(id) DO UPDATE SET
                        project_id = COALESCE(excluded.project_id, sessions.project_id),
                        status = excluded.status,
                        updated_at = excluded.updated_at,
                        metadata_json = excluded.metadata_json
                    """,
                    (sid, p_id, st, final_created, final_updated, meta_json),
                )
                conn.execute("COMMIT")
            except Exception:
                conn.execute("ROLLBACK")
                raise

        # Save artifacts if provided
        if arts:
            self.save_artifacts(sid, arts)

        # Save project_ir if provided
        if p_ir:
            self.save_project_ir(sid, p_ir)

        return self.get_session(sid) or {
            "id": sid,
            "session_id": sid,
            "project_id": p_id,
            "status": st,
            "created_at": final_created,
            "updated_at": final_updated,
            "metadata": meta,
            "artifacts": arts or {},
            "project_ir": p_ir,
        }

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetch full session record including metadata, generated artifacts, and ProjectIR.
        Unpacks metadata keys to top-level for backwards compatibility with ACTIVE_SESSIONS dict.
        """
        conn = self.get_connection()
        cur = conn.execute(
            "SELECT id, project_id, status, created_at, updated_at, metadata_json FROM sessions WHERE id = ?",
            (session_id,),
        )
        row = cur.fetchone()
        if not row:
            return None

        # Parse metadata
        meta: Dict[str, Any] = {}
        if row["metadata_json"]:
            try:
                meta = json.loads(row["metadata_json"])
            except Exception:
                meta = {}

        # Fetch artifacts
        artifact_collection = self.get_artifacts(session_id)
        artifacts_map = artifact_collection.to_dict()

        # Fetch project_ir
        ir_record = self.get_project_ir(session_id)

        session_dict: Dict[str, Any] = {
            "id": row["id"],
            "session_id": row["id"],
            "project_id": row["project_id"],
            "status": row["status"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
            "metadata": meta,
            "artifacts": artifacts_map,
            "artifact_records": list(artifact_collection),
            "project_ir": ir_record,
        }

        # Flatten metadata properties into root level for full compatibility
        for k, v in meta.items():
            if k not in session_dict:
                session_dict[k] = v

        return session_dict

    def list_sessions(
        self,
        project_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """List sessions ordered by created_at DESC with optional filtering."""
        conn = self.get_connection()
        query = "SELECT id, project_id, status, created_at, updated_at, metadata_json FROM sessions WHERE 1=1"
        params: List[Any] = []

        if project_id:
            query += " AND project_id = ?"
            params.append(project_id)
        if status:
            query += " AND status = ?"
            params.append(status)

        query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        cur = conn.execute(query, tuple(params))
        results = []
        for row in cur.fetchall():
            meta = {}
            if row["metadata_json"]:
                try:
                    meta = json.loads(row["metadata_json"])
                except Exception:
                    pass
            item = {
                "id": row["id"],
                "session_id": row["id"],
                "project_id": row["project_id"],
                "status": row["status"],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
                "metadata": meta,
            }
            # Flatten metadata into root
            for k, v in meta.items():
                if k not in item:
                    item[k] = v
            results.append(item)
        return results

    def delete_session(self, session_id: str) -> bool:
        """Delete a session by ID. Cascades to artifacts and project_ir."""
        with self._lock:
            conn = self.get_connection()
            conn.execute("BEGIN IMMEDIATE")
            try:
                cur = conn.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
                deleted = cur.rowcount > 0
                conn.execute("COMMIT")
                return deleted
            except Exception:
                conn.execute("ROLLBACK")
                raise

    # =========================================================================
    # ARTIFACTS CRUD
    # =========================================================================

    def save_artifacts(
        self,
        session_id: str,
        artifacts: Union[Dict[str, str], List[Dict[str, Any]]],
        version: int = 1,
    ) -> List[Dict[str, Any]]:
        """
        Save artifacts for a session.

        Accepts either:
        - dict: {"PRD.md": "# PRD...", "Architecture.md": "..."}
        - list: [{"doc_type": "PRD.md", "content": "...", "version": 1}, ...]
        """
        now = time.time()
        saved_records: List[Dict[str, Any]] = []

        # Standardize items
        items: List[Dict[str, Any]] = []
        if isinstance(artifacts, dict):
            for doc_type, content in artifacts.items():
                items.append({
                    "id": f"{session_id}_{doc_type}_v{version}",
                    "doc_type": str(doc_type),
                    "content": str(content),
                    "version": version,
                    "created_at": now,
                })
        elif isinstance(artifacts, list):
            for art in artifacts:
                doc_type = str(art.get("doc_type", "document.md"))
                v = int(art.get("version", version))
                items.append({
                    "id": art.get("id") or f"{session_id}_{doc_type}_v{v}",
                    "doc_type": doc_type,
                    "content": str(art.get("content", "")),
                    "version": v,
                    "created_at": float(art.get("created_at", now)),
                })

        with self._lock:
            conn = self.get_connection()
            conn.execute("BEGIN IMMEDIATE")
            try:
                # Ensure session exists to avoid FK error
                conn.execute(
                    """
                    INSERT OR IGNORE INTO sessions (id, status, created_at, updated_at, metadata_json)
                    VALUES (?, 'active', ?, ?, '{}')
                    """,
                    (session_id, now, now),
                )

                for item in items:
                    conn.execute(
                        """
                        INSERT INTO artifacts (id, session_id, doc_type, content, version, created_at)
                        VALUES (?, ?, ?, ?, ?, ?)
                        ON CONFLICT(id) DO UPDATE SET
                            content = excluded.content,
                            version = excluded.version,
                            created_at = excluded.created_at
                        """,
                        (item["id"], session_id, item["doc_type"], item["content"], item["version"], item["created_at"]),
                    )
                    saved_records.append({
                        "id": item["id"],
                        "session_id": session_id,
                        "doc_type": item["doc_type"],
                        "content": item["content"],
                        "version": item["version"],
                        "created_at": item["created_at"],
                    })

                conn.execute("COMMIT")
            except Exception:
                conn.execute("ROLLBACK")
                raise

        return saved_records

    def get_artifacts(
        self,
        session_id: str,
        doc_type: Optional[str] = None,
        version: Optional[int] = None,
        as_dict: bool = False,
    ) -> Union[ArtifactCollection, Dict[str, str]]:
        """
        Retrieve artifacts for a session.
        Returns an ArtifactCollection (dual list/dict) or a plain dict if as_dict=True.
        """
        conn = self.get_connection()
        query = "SELECT id, session_id, doc_type, content, version, created_at FROM artifacts WHERE session_id = ?"
        params: List[Any] = [session_id]

        if doc_type:
            query += " AND doc_type = ?"
            params.append(doc_type)
        if version is not None:
            query += " AND version = ?"
            params.append(version)

        query += " ORDER BY version ASC, created_at ASC"
        cur = conn.execute(query, tuple(params))
        records = [dict(row) for row in cur.fetchall()]

        if as_dict:
            return {r["doc_type"]: r["content"] for r in records}
        return ArtifactCollection(records)

    # =========================================================================
    # PROJECT IR CRUD
    # =========================================================================

    def save_project_ir(
        self,
        session_id: str,
        ir_data: Union[str, Dict[str, Any], Any],
        schema_version: str = "1.0.0",
    ) -> Dict[str, Any]:
        """
        Persist Canonical ProjectIR JSON representation for a session.
        Handles Pydantic models, Python dicts, and raw JSON strings.
        """
        now = time.time()

        # Serialize to JSON string
        if hasattr(ir_data, "model_dump_json"):
            ir_json = ir_data.model_dump_json()
        elif hasattr(ir_data, "model_dump"):
            ir_json = json.dumps(ir_data.model_dump())
        elif isinstance(ir_data, dict):
            ir_json = json.dumps(ir_data)
        elif isinstance(ir_data, str):
            ir_json = ir_data
        else:
            ir_json = json.dumps(ir_data, default=str)

        with self._lock:
            conn = self.get_connection()
            conn.execute("BEGIN IMMEDIATE")
            try:
                # Ensure session exists to avoid FK error
                conn.execute(
                    """
                    INSERT OR IGNORE INTO sessions (id, status, created_at, updated_at, metadata_json)
                    VALUES (?, 'active', ?, ?, '{}')
                    """,
                    (session_id, now, now),
                )

                conn.execute(
                    """
                    INSERT INTO project_ir (session_id, schema_version, ir_json, updated_at)
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT(session_id) DO UPDATE SET
                        schema_version = excluded.schema_version,
                        ir_json = excluded.ir_json,
                        updated_at = excluded.updated_at
                    """,
                    (session_id, schema_version, ir_json, now),
                )
                conn.execute("COMMIT")
            except Exception:
                conn.execute("ROLLBACK")
                raise

        return {
            "session_id": session_id,
            "schema_version": schema_version,
            "ir_json": ir_json,
            "updated_at": now,
        }

    def get_project_ir(
        self,
        session_id: str,
        as_model: bool = False,
    ) -> Optional[Any]:
        """
        Retrieve ProjectIR for a session.
        Returns ProjectIRRecord (or Pydantic model if as_model=True).
        """
        conn = self.get_connection()
        cur = conn.execute(
            "SELECT session_id, schema_version, ir_json, updated_at FROM project_ir WHERE session_id = ?",
            (session_id,),
        )
        row = cur.fetchone()
        if not row:
            return None

        try:
            parsed = json.loads(row["ir_json"])
        except Exception:
            parsed = {}

        if as_model:
            try:
                from src.models.project_ir import ProjectIR
                return ProjectIR.model_validate(parsed)
            except Exception as e:
                logger.warning("Could not instantiate ProjectIR model: %s", e)

        return ProjectIRRecord(
            data=parsed,
            schema_version=row["schema_version"],
            ir_json=row["ir_json"],
            session_id=row["session_id"],
            updated_at=row["updated_at"],
        )

    # =========================================================================
    # RAG CHUNKS CRUD
    # =========================================================================

    def add_rag_chunk(
        self,
        content: str,
        source: str = "",
        session_id: Optional[str] = None,
        metadata: Optional[Union[str, Dict[str, Any]]] = None,
        id: Optional[str] = None,
        chunk_id: Optional[str] = None,
        created_at: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Add or update an indexed RAG chunk."""
        now = time.time()
        c_at = created_at if created_at is not None else now
        cid = id or chunk_id or f"chunk_{uuid.uuid4().hex[:12]}"

        if isinstance(metadata, dict):
            meta_json = json.dumps(metadata)
        elif isinstance(metadata, str):
            meta_json = metadata
        else:
            meta_json = "{}"

        with self._lock:
            conn = self.get_connection()
            conn.execute("BEGIN IMMEDIATE")
            try:
                # If session_id provided, ensure session exists
                if session_id:
                    conn.execute(
                        """
                        INSERT OR IGNORE INTO sessions (id, status, created_at, updated_at, metadata_json)
                        VALUES (?, 'active', ?, ?, '{}')
                        """,
                        (session_id, now, now),
                    )

                conn.execute(
                    """
                    INSERT INTO rag_chunks (id, session_id, content, source, metadata_json, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                    ON CONFLICT(id) DO UPDATE SET
                        session_id = excluded.session_id,
                        content = excluded.content,
                        source = excluded.source,
                        metadata_json = excluded.metadata_json,
                        created_at = excluded.created_at
                    """,
                    (cid, session_id, content, source, meta_json, c_at),
                )
                conn.execute("COMMIT")
            except Exception:
                conn.execute("ROLLBACK")
                raise

        meta_parsed = {}
        try:
            meta_parsed = json.loads(meta_json)
        except Exception:
            pass

        return {
            "id": cid,
            "session_id": session_id,
            "content": content,
            "source": source,
            "metadata": meta_parsed,
            "created_at": c_at,
        }

    def get_rag_chunks(
        self,
        session_id: Optional[str] = None,
        source: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """Retrieve indexed RAG chunks with optional filtering."""
        conn = self.get_connection()
        query = "SELECT id, session_id, content, source, metadata_json, created_at FROM rag_chunks WHERE 1=1"
        params: List[Any] = []

        if session_id:
            query += " AND session_id = ?"
            params.append(session_id)
        if source:
            query += " AND source = ?"
            params.append(source)

        query += " ORDER BY created_at ASC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        cur = conn.execute(query, tuple(params))
        results = []
        for row in cur.fetchall():
            meta = {}
            if row["metadata_json"]:
                try:
                    meta = json.loads(row["metadata_json"])
                except Exception:
                    pass
            results.append({
                "id": row["id"],
                "session_id": row["session_id"],
                "content": row["content"],
                "source": row["source"],
                "metadata": meta,
                "created_at": row["created_at"],
            })
        return results


class PersistentSessionDict(dict):
    """
    Dict-compatible interface wrapping SQLiteStore.
    Maintains 100% compatibility with legacy in-memory ACTIVE_SESSIONS dict while
    ensuring all sessions and artifacts are persistently stored in SQLite.
    """

    def __init__(self, store: SQLiteStore):
        super().__init__()
        self._store = store

    def __getitem__(self, key: str) -> Dict[str, Any]:
        sess = self._store.get_session(key)
        if sess is None:
            raise KeyError(key)
        super().__setitem__(key, sess)
        return sess

    def __setitem__(self, key: str, value: Dict[str, Any]):
        super().__setitem__(key, value)
        try:
            meta = {
                k: v for k, v in value.items()
                if k not in (
                    "session_id", "id", "project_id", "status", "artifacts",
                    "artifact_records", "project_ir", "created_at", "updated_at", "metadata"
                )
            }
            raw_meta = value.get("metadata")
            if isinstance(raw_meta, dict):
                meta.update(raw_meta)
            self._store.save_session(
                session_id=key,
                project_id=value.get("project_id"),
                status=value.get("status", "completed"),
                metadata=meta,
                artifacts=value.get("artifacts"),
                project_ir=value.get("project_ir"),
                created_at=value.get("created_at"),
                updated_at=value.get("updated_at"),
            )
        except Exception as e:
            logger.warning("Error persisting session '%s' to SQLite: %s", key, e)

    def __contains__(self, key: object) -> bool:
        if not isinstance(key, str):
            return False
        if super().__contains__(key):
            return True
        return self._store.get_session(key) is not None

    def get(self, key: str, default: Any = None) -> Any:
        try:
            return self[key]
        except KeyError:
            return default

    def pop(self, key: str, *args: Any) -> Any:
        if super().__contains__(key):
            res = super().pop(key)
        else:
            res = None
        self._store.delete_session(key)
        if res is not None:
            return res
        if args:
            return args[0]
        return None

    def __delitem__(self, key: str):
        if super().__contains__(key):
            super().__delitem__(key)
        self._store.delete_session(key)

    def clear(self):
        super().clear()
        self._store.clear_all()

    def keys(self) -> Any:
        sessions = self._store.list_sessions(limit=1000)
        return [s["session_id"] for s in sessions]

    def values(self) -> Any:
        sessions = self._store.list_sessions(limit=1000)
        return [self._store.get_session(s["session_id"]) for s in sessions]

    def items(self) -> Any:
        sessions = self._store.list_sessions(limit=1000)
        return [(s["session_id"], self._store.get_session(s["session_id"])) for s in sessions]

    def __len__(self) -> int:
        return self._store.get_stats().get("sessions", 0)

    def __iter__(self) -> Iterator[str]:
        return iter(self.keys())
