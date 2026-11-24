"""
tests/test_sqlite_store.py
Comprehensive unit test suite for VoGenFlow's SQLite WAL-mode persistent storage adapter.

Covers:
1. SQLite WAL mode and PRAGMA settings (WAL, NORMAL synchronous, foreign_keys=ON)
2. Projects CRUD & constraints
3. Sessions CRUD & metadata JSON serialization/deserialization
4. Artifacts CRUD (doc_type, versioning, dual list/dict access)
5. ProjectIR Canonical JSON persistence & Pydantic model validation
6. RAG Chunks indexing and query filtering
7. Multi-threaded concurrent write resilience and transaction isolation
8. Foreign key cascade deletion integrity
9. PersistentSessionDict compatibility layer
"""

import os
import json
import time
import shutil
import tempfile
import threading
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

import pytest

from src.db.sqlite_store import (
    SQLiteStore,
    PersistentSessionDict,
    ArtifactCollection,
    ProjectIRRecord,
)
from src.models.project_ir import (
    ProjectIR,
    Persona,
    Requirement,
    SLAMetric,
    ThreatEntry,
    ArchitectureSpec,
    DatabaseModel,
    APIContract,
    LifecycleSpec,
    FailureRecoveryRow,
    TaskMilestone,
    TaskItem,
)


@pytest.fixture
def temp_db_path():
    """Create a temporary file path for a test database."""
    temp_dir = tempfile.mkdtemp(prefix="vogenflow_test_db_")
    db_file = os.path.join(temp_dir, "test_vogenflow.db")
    yield db_file
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def file_store(temp_db_path):
    """File-backed SQLiteStore instance."""
    store = SQLiteStore(db_path=temp_db_path)
    yield store
    store.close()


@pytest.fixture
def mem_store():
    """In-memory SQLiteStore instance."""
    store = SQLiteStore(db_path=":memory:")
    yield store
    store.close()


# ==============================================================================
# 1. PRAGMA & WAL MODE VERIFICATION
# ==============================================================================

class TestPragmasAndWALMode:
    """Validate SQLite WAL mode, foreign keys, and synchronous pragma settings."""

    def test_file_db_wal_mode(self, file_store):
        """Verify journal_mode is WAL and synchronous is NORMAL on disk file."""
        assert file_store.is_wal_mode()
        assert file_store.get_journal_mode() == "WAL"

        conn = file_store.get_connection()
        cur = conn.execute("PRAGMA synchronous;")
        sync_mode = cur.fetchone()[0]
        # NORMAL mode is integer 1
        assert sync_mode in (1, "1", "NORMAL")

        cur = conn.execute("PRAGMA foreign_keys;")
        fk = cur.fetchone()[0]
        assert fk == 1

    def test_memory_db_pragmas(self, mem_store):
        """In-memory DB uses MEMORY journal mode with foreign keys enabled."""
        assert mem_store.is_wal_mode()
        conn = mem_store.get_connection()
        cur = conn.execute("PRAGMA foreign_keys;")
        assert cur.fetchone()[0] == 1


# ==============================================================================
# 2. PROJECTS CRUD
# ==============================================================================

class TestProjectsCRUD:
    """Test project creation, retrieval, listing, and deletion."""

    def test_save_and_get_project(self, file_store):
        proj = file_store.save_project(
            id="proj_alpha",
            name="Alpha Platform",
            description="High-throughput distributed engine",
        )
        assert proj["id"] == "proj_alpha"
        assert proj["name"] == "Alpha Platform"
        assert proj["description"] == "High-throughput distributed engine"

        fetched = file_store.get_project("proj_alpha")
        assert fetched is not None
        assert fetched["name"] == "Alpha Platform"

    def test_update_project(self, file_store):
        file_store.save_project(id="proj_up", name="Original Name")
        updated = file_store.save_project(id="proj_up", name="Updated Name", description="New description")
        assert updated["name"] == "Updated Name"
        assert updated["description"] == "New description"

    def test_list_and_delete_project(self, file_store):
        file_store.save_project(id="p1", name="Project 1")
        file_store.save_project(id="p2", name="Project 2")
        projects = file_store.list_projects()
        assert len(projects) >= 2

        deleted = file_store.delete_project("p1")
        assert deleted is True
        assert file_store.get_project("p1") is None
        assert file_store.delete_project("nonexistent") is False


# ==============================================================================
# 3. SESSIONS CRUD & SERIALIZATION
# ==============================================================================

class TestSessionsCRUD:
    """Test session creation, updating, retrieval, and metadata serialization."""

    def test_save_session_kwargs(self, file_store):
        file_store.save_project(id="proj_1", name="Project One")
        session = file_store.save_session(
            session_id="sess_001",
            project_id="proj_1",
            status="completed",
            metadata={
                "transcript": "Design an enterprise RAG microservice with BM25 hybrid search.",
                "preset": "standard",
                "telemetry": {"latency_ms": 124.5, "tokens": 450},
            },
        )
        assert session["id"] == "sess_001"
        assert session["status"] == "completed"
        assert session["transcript"] == "Design an enterprise RAG microservice with BM25 hybrid search."
        assert session["telemetry"]["tokens"] == 450

    def test_save_session_dict_format(self, file_store):
        """Verify saving via dictionary format matches ACTIVE_SESSIONS payload."""
        payload = {
            "session_id": "sess_dict_002",
            "transcript": "Deploy Kubernetes clusters with ArgoCD gitops.",
            "preset": "lean_sprint",
            "status": "active",
            "artifacts": {
                "PRD.md": "# PRD for ArgoCD Pipeline",
                "Architecture.md": "# Architecture Overview",
            },
            "telemetry": {"consensus_score": 0.98},
            "duration": 5.4,
            "saved_paths": ["/output/PRD.md"],
        }
        res = file_store.save_session(payload)
        assert res["session_id"] == "sess_dict_002"
        assert res["artifacts"]["PRD.md"] == "# PRD for ArgoCD Pipeline"

        # Fetch independently
        fetched = file_store.get_session("sess_dict_002")
        assert fetched is not None
        assert fetched["transcript"] == "Deploy Kubernetes clusters with ArgoCD gitops."
        assert fetched["preset"] == "lean_sprint"
        assert "PRD.md" in fetched["artifacts"]
        assert fetched["duration"] == 5.4

    def test_list_sessions_and_filtering(self, file_store):
        file_store.save_project(id="proj_a", name="Proj A")
        file_store.save_project(id="proj_b", name="Proj B")

        file_store.save_session("s_a1", project_id="proj_a", status="completed")
        file_store.save_session("s_a2", project_id="proj_a", status="active")
        file_store.save_session("s_b1", project_id="proj_b", status="completed")

        all_sess = file_store.list_sessions()
        assert len(all_sess) >= 3

        proj_a_sess = file_store.list_sessions(project_id="proj_a")
        assert len(proj_a_sess) == 2

        completed_sess = file_store.list_sessions(status="completed")
        assert len(completed_sess) >= 2

    def test_delete_session_and_cascade(self, file_store):
        """Deleting a session cascades to its artifacts and project_ir."""
        file_store.save_session(
            session_id="sess_cascade",
            artifacts={"PRD.md": "# To be deleted", "Architecture.md": "# Deleted"},
            project_ir={"project_name": "Doomed Project"},
        )
        assert file_store.get_session("sess_cascade") is not None
        assert len(file_store.get_artifacts("sess_cascade")) == 2

        deleted = file_store.delete_session("sess_cascade")
        assert deleted is True
        assert file_store.get_session("sess_cascade") is None
        assert len(file_store.get_artifacts("sess_cascade")) == 0
        assert file_store.get_project_ir("sess_cascade") is None


# ==============================================================================
# 4. ARTIFACTS CRUD & DUAL ACCESS
# ==============================================================================

class TestArtifactsCRUD:
    """Test saving artifacts, versioning, and dual list/dict access."""

    def test_save_artifacts_dict(self, file_store):
        arts = {
            "PRD.md": "# Product Requirements",
            "Architecture.md": "# System Architecture",
            "Flow.md": "sequenceDiagram\nClient->>Server: HTTP",
        }
        saved = file_store.save_artifacts("sess_art_1", arts)
        assert len(saved) == 3

        collection = file_store.get_artifacts("sess_art_1")
        assert isinstance(collection, ArtifactCollection)
        assert len(collection) == 3
        # Dual list/dict access
        assert "PRD.md" in collection
        assert collection["PRD.md"] == "# Product Requirements"
        assert collection.get("Architecture.md") == "# System Architecture"
        assert collection.get("NonExistent.md") is None

        # As dict
        dict_view = file_store.get_artifacts("sess_art_1", as_dict=True)
        assert isinstance(dict_view, dict)
        assert dict_view["Flow.md"] == "sequenceDiagram\nClient->>Server: HTTP"

    def test_artifact_versioning(self, file_store):
        file_store.save_artifacts("sess_art_v", {"PRD.md": "v1 content"}, version=1)
        file_store.save_artifacts("sess_art_v", {"PRD.md": "v2 content"}, version=2)

        v1 = file_store.get_artifacts("sess_art_v", doc_type="PRD.md", version=1)
        assert len(v1) == 1
        assert v1[0]["content"] == "v1 content"

        v2 = file_store.get_artifacts("sess_art_v", doc_type="PRD.md", version=2)
        assert len(v2) == 1
        assert v2[0]["content"] == "v2 content"


# ==============================================================================
# 5. PROJECT IR PERSISTENCE & PYDANTIC VALIDATION
# ==============================================================================

class TestProjectIRPersistence:
    """Test persistence and retrieval of canonical ProjectIR representations."""

    def test_save_project_ir_from_model(self, file_store):
        ir = ProjectIR(
            project_name="VoGenFlow Enterprise",
            tagline="Voice-to-Architecture in seconds",
            executive_summary="Production-grade distributed specification synthesizer.",
            target_personas=[
                Persona(name="Lead Architect", role="Infrastructure planning", pain_points=["Manual PRDs"], needs=["Auto DDL"])
            ],
            requirements=[
                Requirement(id="REQ-001", title="SQLite WAL persistence", priority="P0")
            ],
            non_functional_slas=[
                SLAMetric(metric="Persistence Latency", target="< 10ms", verification_method="Unit Test")
            ],
            security_threat_matrix=[
                ThreatEntry(threat_category="Tampering", threat_description="SQL injection", mitigation="Parameterized queries")
            ],
            architecture=ArchitectureSpec(
                overview="Microservice gateway with SQLite WAL storage",
                topology_mermaid="graph TD\nClient-->API\nAPI-->SQLite",
                database_ddl="CREATE TABLE test (id INT);",
                database_models=[DatabaseModel(table_name="test", description="Test model")],
                api_contracts=[APIContract(endpoint="POST /deliberate", description="Council execution")]
            ),
            lifecycle=LifecycleSpec(
                sequence_diagram_mermaid="sequenceDiagram\nClient->>Server: Done",
                failure_recovery_matrix=[
                    FailureRecoveryRow(
                        component="Database",
                        detection_sla="< 1.5s",
                        recovery_mechanism="Auto-restart connection pool with exponential backoff"
                    )
                ]
            ),
            tasks=[
                TaskMilestone(
                    milestone_id="M1",
                    title="Domain Models & Database Schemas",
                    tasks=[TaskItem(description="Write SQLite persistent store adapter")]
                )
            ],
        )

        res = file_store.save_project_ir("sess_ir_test", ir)
        assert res["session_id"] == "sess_ir_test"

        # Fetch as record
        rec = file_store.get_project_ir("sess_ir_test")
        assert isinstance(rec, ProjectIRRecord)
        assert rec["project_name"] == "VoGenFlow Enterprise"
        assert rec.schema_version == "1.0.0"

        # Fetch as validated Pydantic model
        model = file_store.get_project_ir("sess_ir_test", as_model=True)
        assert isinstance(model, ProjectIR)
        assert model.project_name == "VoGenFlow Enterprise"
        assert model.requirements[0].id == "REQ-001"

    def test_save_project_ir_raw_json(self, file_store):
        raw_json = json.dumps({"project_name": "Raw JSON Project", "version": "beta"})
        file_store.save_project_ir("sess_raw", raw_json, schema_version="2.1.0")

        fetched = file_store.get_project_ir("sess_raw")
        assert fetched["project_name"] == "Raw JSON Project"
        assert fetched.schema_version == "2.1.0"


# ==============================================================================
# 6. RAG CHUNKS CRUD
# ==============================================================================

class TestRAGChunksCRUD:
    """Test indexing, tagging, and retrieving technical RAG knowledge chunks."""

    def test_add_and_get_rag_chunks(self, file_store):
        c1 = file_store.add_rag_chunk(
            content="FastAPI uses Starlette under the hood for async ASGI routing.",
            source="fastapi_docs.md",
            session_id="sess_rag",
            metadata={"framework": "fastapi", "category": "backend"},
        )
        assert c1["id"].startswith("chunk_")

        c2 = file_store.add_rag_chunk(
            content="PostgreSQL Row Level Security (RLS) restricts row access by tenant_id.",
            source="postgres_security.md",
            session_id="sess_rag",
            metadata={"database": "postgres", "category": "security"},
        )

        # Retrieve all for session
        chunks = file_store.get_rag_chunks(session_id="sess_rag")
        assert len(chunks) == 2
        assert any("Starlette" in ch["content"] for ch in chunks)

        # Filter by source
        source_chunks = file_store.get_rag_chunks(source="postgres_security.md")
        assert len(source_chunks) == 1
        assert source_chunks[0]["metadata"]["database"] == "postgres"


# ==============================================================================
# 7. CONCURRENT WRITES & MULTI-THREADING STABILITY
# ==============================================================================

class TestConcurrencyAndThreadSafety:
    """Stress-test concurrent transactions across multiple threads in SQLite WAL mode."""

    def test_concurrent_session_writes(self, file_store):
        """Spawn 12 concurrent worker threads saving sessions and artifacts simultaneously."""
        num_threads = 12
        iterations = 5

        def _worker(thread_id: int):
            for i in range(iterations):
                sid = f"concur_{thread_id}_{i}"
                file_store.save_session(
                    session_id=sid,
                    status="completed",
                    metadata={"worker": thread_id, "iteration": i, "timestamp": time.time()},
                    artifacts={
                        "PRD.md": f"# PRD for Thread {thread_id} Iteration {i}",
                        "Architecture.md": f"# Arch for Thread {thread_id} Iteration {i}",
                    },
                )
                file_store.add_rag_chunk(
                    content=f"Knowledge chunk generated by worker {thread_id} in round {i}",
                    source=f"worker_{thread_id}.log",
                    session_id=sid,
                )

        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(_worker, tid) for tid in range(num_threads)]
            for f in futures:
                f.result()

        stats = file_store.get_stats()
        expected_sessions = num_threads * iterations
        assert stats["sessions"] == expected_sessions
        assert stats["artifacts"] == expected_sessions * 2
        assert stats["rag_chunks"] == expected_sessions


# ==============================================================================
# 8. PERSISTENT SESSION DICT COMPATIBILITY
# ==============================================================================

class TestPersistentSessionDict:
    """Verify dictionary interface proxying to SQLiteStore."""

    def test_dict_operations(self, file_store):
        proxy = PersistentSessionDict(file_store)

        # Assignment saves to SQLite
        proxy["sess_proxy_1"] = {
            "session_id": "sess_proxy_1",
            "transcript": "Build microservices with Go and gRPC.",
            "preset": "standard",
            "artifacts": {"PRD.md": "# Go Microservices"},
        }

        # Check contains
        assert "sess_proxy_1" in proxy
        assert "nonexistent_sid" not in proxy

        # Check retrieval
        data = proxy["sess_proxy_1"]
        assert data["session_id"] == "sess_proxy_1"
        assert data["transcript"] == "Build microservices with Go and gRPC."
        assert data["artifacts"]["PRD.md"] == "# Go Microservices"

        # Direct DB check
        direct = file_store.get_session("sess_proxy_1")
        assert direct is not None
        assert direct["transcript"] == "Build microservices with Go and gRPC."

        # Dict keys and len
        assert "sess_proxy_1" in proxy.keys()
        assert len(proxy) >= 1

        # Deletion
        del proxy["sess_proxy_1"]
        assert "sess_proxy_1" not in proxy
        assert file_store.get_session("sess_proxy_1") is None

    def test_metadata_dict_preservation(self, file_store):
        """Verify that nested metadata dict is properly preserved by PersistentSessionDict."""
        proxy = PersistentSessionDict(file_store)
        proxy["sess_meta_1"] = {
            "session_id": "sess_meta_1",
            "status": "completed",
            "metadata": {"custom_tag": "fintech", "priority": "high"},
            "author": "Alice",
        }

        # Check retrieval via proxy and direct store
        direct = file_store.get_session("sess_meta_1")
        assert direct is not None
        assert direct["metadata"]["custom_tag"] == "fintech"
        assert direct["metadata"]["priority"] == "high"
        assert direct["metadata"]["author"] == "Alice"

    def test_persistent_session_dict_read_modify_write_roundtrip(self, temp_db_path):
        """Verify read-modify-write updates to nested metadata persist across fresh SQLiteStore instances."""
        store1 = SQLiteStore(temp_db_path)
        proxy1 = PersistentSessionDict(store1)
        proxy1["meta_complex"] = {
            "session_id": "meta_complex",
            "status": "active",
            "metadata": {
                "tags": ["alpha", "beta"],
                "custom_flags": {"enable_rls": True, "max_retries": 5},
            },
            "transcript": "Original transcript",
        }

        # Read-modify-write: mutate nested metadata (which get_session also flattened to top-level)
        rec = proxy1["meta_complex"]
        rec["metadata"]["tags"] = ["gamma", "delta"]
        rec["metadata"]["custom_flags"] = {"enable_rls": False, "new_key": "added"}
        proxy1["meta_complex"] = rec

        store2 = SQLiteStore(temp_db_path)
        reloaded = store2.get_session("meta_complex")
        assert reloaded is not None
        assert reloaded["metadata"]["tags"] == ["gamma", "delta"]
        assert reloaded["metadata"]["custom_flags"] == {"enable_rls": False, "new_key": "added"}
        assert reloaded["transcript"] == "Original transcript"
        store1.close()
        store2.close()

    def test_save_session_dict_preserves_metadata_and_extra_keys(self, temp_db_path):
        """Verify save_session(dict) preserves both explicit metadata and extra top-level keys."""
        store = SQLiteStore(temp_db_path)
        store.save_session({
            "session_id": "meta_both",
            "status": "active",
            "metadata": {"nested": {"x": 1}, "preset": "override_preset"},
            "transcript": "Voice transcript here",
            "preset": "standard",
        })
        loaded = store.get_session("meta_both")
        assert loaded is not None
        assert loaded["metadata"]["nested"] == {"x": 1}
        assert loaded["transcript"] == "Voice transcript here"
        assert loaded["metadata"]["preset"] == "override_preset"

        # Non-dict metadata should not raise or drop extra keys
        proxy = PersistentSessionDict(store)
        proxy["meta_bad_type"] = {
            "session_id": "meta_bad_type",
            "status": "active",
            "metadata": "not_a_dict",
            "author": "Bob",
        }
        bad_loaded = store.get_session("meta_bad_type")
        assert bad_loaded is not None
        assert bad_loaded["metadata"]["author"] == "Bob"
        store.close()
