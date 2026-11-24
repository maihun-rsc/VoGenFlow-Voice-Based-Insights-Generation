"""
src/mcp/server.py
Production-Grade Model Context Protocol (MCP) Server for VoGenFlow.

Exposes Canonical ProjectIR, Generated Specifications (PRD, Architecture, Flow, Tasks, Design),
Raw Executable PostgreSQL/Supabase SQL DDL, Phased Tasks, and Grounded Knowledge Retrieval
to downstream coding agents (Cursor, Claude Code, Antigravity).
"""

import os
import re
import sys
import json
import time
import logging
import warnings
from pathlib import Path
from typing import Dict, Any, Optional, List, Union, Tuple

# Ensure repository root is on sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# Suppress harmless pydantic-settings unresolved forward reference warning on lifespan
warnings.filterwarnings("ignore", message=".*Field 'lifespan'.*")
warnings.filterwarnings("ignore", category=UserWarning)

from mcp.server.fastmcp import FastMCP

from src.config import Config
from src.models.project_ir import ProjectIR, create_project_ir_from_council_artifacts
from src.knowledge_db import CuratedKnowledgeDB
from src.rag_engine import LocalRAGEngine

# Configure logger
logger = logging.getLogger("vogenflow.mcp")
if not logger.handlers:
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s"))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

SAFE_SESSION_RE = re.compile(r"^[a-zA-Z0-9_\-]+$")


class VoGenFlowResolver:
    """
    Central storage and document resolver for the VoGenFlow MCP Server.
    Provides uniform access across:
    1. Persistent SQLiteStore (src.db.sqlite_store)
    2. In-memory active sessions (src.api.server.ACTIVE_SESSIONS)
    3. Filesystem artifact directories (output/sessions/{session_id})
    """

    DOC_TYPE_MAPPING = {
        "prd": "PRD.md",
        "prd.md": "PRD.md",
        "requirements": "PRD.md",
        "product": "PRD.md",
        "architecture": "Architecture.md",
        "architecture.md": "Architecture.md",
        "arch": "Architecture.md",
        "system": "Architecture.md",
        "flow": "Flow.md",
        "flow.md": "Flow.md",
        "lifecycle": "Flow.md",
        "sequence": "Flow.md",
        "tasks": "tasks.md",
        "tasks.md": "tasks.md",
        "task": "tasks.md",
        "roadmap": "tasks.md",
        "todo": "tasks.md",
        "design": "design_proposal.md",
        "design.md": "design_proposal.md",
        "design_proposal": "design_proposal.md",
        "design_proposal.md": "design_proposal.md",
        "ui": "design_proposal.md",
        "ux": "design_proposal.md",
        "bundle": "master_execution_bundle.md",
        "master": "master_execution_bundle.md",
        "master_execution_bundle.md": "master_execution_bundle.md",
    }

    def __init__(
        self,
        base_dir: Optional[Union[str, Path]] = None,
        output_dir: Optional[Union[str, Path]] = None,
        db_path: Optional[Union[str, Path]] = None,
    ):
        if base_dir is None:
            self.base_dir = Path(__file__).resolve().parent.parent.parent
        else:
            self.base_dir = Path(base_dir).resolve()

        if output_dir is None:
            self.output_dir = getattr(Config, "OUTPUT_DIR", self.base_dir / "output")
        else:
            self.output_dir = Path(output_dir).resolve()

        self.sessions_dir = self.output_dir / "sessions"
        self.db_path = db_path or os.getenv("VOGENFLOW_DB_PATH") or (self.output_dir / "vogenflow.db")

        self._store = None
        self._knowledge_db = None
        self._rag_engine = None

    @property
    def store(self):
        """Lazy-loaded SQLiteStore adapter."""
        if self._store is None:
            try:
                from src.db.sqlite_store import SQLiteStore
                self._store = SQLiteStore(db_path=self.db_path)
            except Exception as e:
                logger.debug("SQLiteStore not available or could not be loaded: %s", e)
                self._store = None
        return self._store

    @property
    def knowledge_db(self) -> CuratedKnowledgeDB:
        """Lazy-loaded CuratedKnowledgeDB."""
        if self._knowledge_db is None:
            self._knowledge_db = CuratedKnowledgeDB()
        return self._knowledge_db

    @property
    def rag_engine(self) -> LocalRAGEngine:
        """Lazy-loaded LocalRAGEngine."""
        if self._rag_engine is None:
            try:
                self._rag_engine = LocalRAGEngine()
            except Exception as e:
                logger.debug("LocalRAGEngine initialization error: %s", e)
        return self._rag_engine

    def validate_session_id(self, session_id: str) -> str:
        """Validate session ID against path traversal and safe characters."""
        clean = (session_id or "").strip()
        if not clean or not SAFE_SESSION_RE.match(clean):
            raise ValueError(
                f"Invalid session_id '{session_id}'. Must be alphanumeric with hyphens or underscores only."
            )
        return clean

    def list_sessions(self, limit: int = 50) -> List[Dict[str, Any]]:
        """List all discovered sessions across database, memory, and filesystem."""
        limit = max(0, min(int(limit), 500))
        if limit == 0:
            return []
        sessions_map: Dict[str, Dict[str, Any]] = {}

        # 1. From SQLiteStore if present
        if self.store is not None:
            try:
                db_sessions = self.store.list_sessions(limit=limit)
                for s in db_sessions:
                    sid = s.get("id")
                    if sid:
                        sessions_map[sid] = {
                            "session_id": sid,
                            "source": "sqlite_db",
                            "status": s.get("status", "completed"),
                            "created_at": s.get("created_at", 0.0),
                            "updated_at": s.get("updated_at", 0.0),
                        }
            except Exception as e:
                logger.debug("Error listing sessions from SQLiteStore: %s", e)

        # 2. From ACTIVE_SESSIONS in-memory cache
        try:
            from src.api.server import ACTIVE_SESSIONS
            for sid, sdata in ACTIVE_SESSIONS.items():
                if sid not in sessions_map:
                    sessions_map[sid] = {
                        "session_id": sid,
                        "source": "active_memory",
                        "status": "active",
                        "created_at": sdata.get("created_at", time.time()),
                        "updated_at": sdata.get("created_at", time.time()),
                    }
        except Exception:
            pass

        # 3. From filesystem output/sessions/
        if self.sessions_dir.exists():
            try:
                for entry in self.sessions_dir.iterdir():
                    if entry.is_dir() and SAFE_SESSION_RE.match(entry.name):
                        sid = entry.name
                        if sid not in sessions_map:
                            stat = entry.stat()
                            sessions_map[sid] = {
                                "session_id": sid,
                                "source": "filesystem",
                                "status": "persisted",
                                "created_at": stat.st_ctime,
                                "updated_at": stat.st_mtime,
                            }
            except Exception as e:
                logger.debug("Error scanning sessions directory: %s", e)

        # Sort descending by updated_at / created_at
        sorted_sessions = sorted(
            sessions_map.values(),
            key=lambda x: max(x.get("updated_at", 0.0), x.get("created_at", 0.0)),
            reverse=True,
        )
        return sorted_sessions[:limit]

    def resolve_session_id(self, session_id: Optional[str] = None) -> Optional[str]:
        """Resolve a requested session ID, handling 'latest', None, or explicit IDs."""
        if session_id and session_id.strip().lower() not in ("latest", "current", "default"):
            return self.validate_session_id(session_id.strip())

        # Determine latest session
        sessions = self.list_sessions(limit=1)
        if sessions:
            return sessions[0]["session_id"]
        return None

    def get_session_artifacts(self, session_id: str) -> Dict[str, str]:
        """Fetch all markdown artifacts for a given session."""
        sid = self.validate_session_id(session_id)
        artifacts: Dict[str, str] = {}

        # 1. Try SQLiteStore
        if self.store is not None:
            try:
                col = self.store.get_artifacts(sid)
                if col:
                    artifacts.update(col.to_dict())
            except Exception as e:
                logger.debug("Failed to get artifacts from SQLiteStore for %s: %s", sid, e)

        # 2. Try ACTIVE_SESSIONS
        if not artifacts:
            try:
                from src.api.server import ACTIVE_SESSIONS
                if sid in ACTIVE_SESSIONS and "artifacts" in ACTIVE_SESSIONS[sid]:
                    artifacts.update(ACTIVE_SESSIONS[sid]["artifacts"])
            except Exception:
                pass

        # 3. Try filesystem directory output/sessions/{sid}
        if not artifacts and self.sessions_dir.exists():
            target_dir = self.sessions_dir / sid
            if target_dir.exists() and target_dir.is_dir():
                try:
                    for f in target_dir.glob("*.md"):
                        artifacts[f.name] = f.read_text(encoding="utf-8")
                except Exception as e:
                    logger.debug("Failed to read artifacts from disk for %s: %s", sid, e)

        return artifacts

    def get_project_ir(self, session_id: Optional[str] = None) -> Tuple[Optional[ProjectIR], str]:
        """
        Fetch or reconstruct canonical ProjectIR for a session.
        Returns (project_ir, resolved_session_id).
        """
        sid = self.resolve_session_id(session_id)
        if not sid:
            return None, ""

        # 1. Check SQLiteStore
        if self.store is not None:
            try:
                record = self.store.get_project_ir(sid)
                if record:
                    model = record.to_model()
                    if model is not None:
                        return model, sid
                    if hasattr(record, "ir_json") and record.ir_json:
                        data = json.loads(record.ir_json)
                        return ProjectIR.model_validate(data), sid
            except Exception as e:
                logger.debug("Failed to load ProjectIR from SQLiteStore for %s: %s", sid, e)

        # 2. Check ACTIVE_SESSIONS
        try:
            from src.api.server import ACTIVE_SESSIONS
            if sid in ACTIVE_SESSIONS:
                ir_data = ACTIVE_SESSIONS[sid].get("project_ir")
                if ir_data:
                    if isinstance(ir_data, ProjectIR):
                        return ir_data, sid
                    if isinstance(ir_data, dict):
                        return ProjectIR.model_validate(ir_data), sid
        except Exception:
            pass

        # 3. Check filesystem for project_ir.json
        if self.sessions_dir.exists():
            ir_file = self.sessions_dir / sid / "project_ir.json"
            if ir_file.exists():
                try:
                    content = ir_file.read_text(encoding="utf-8")
                    data = json.loads(content)
                    return ProjectIR.model_validate(data), sid
                except Exception as e:
                    logger.debug("Failed to read project_ir.json for %s: %s", sid, e)

        # 4. Reconstruct from markdown artifacts
        artifacts = self.get_session_artifacts(sid)
        if artifacts:
            try:
                ir = create_project_ir_from_council_artifacts("", artifacts)
                # Cache to disk for instant future reads
                ir_file = self.sessions_dir / sid / "project_ir.json"
                if ir_file.parent.exists() and not ir_file.exists():
                    try:
                        ir_file.write_text(ir.model_dump_json(indent=2), encoding="utf-8")
                    except Exception:
                        pass
                return ir, sid
            except Exception as e:
                logger.warning("Could not reconstruct ProjectIR from artifacts for %s: %s", sid, e)

        return None, sid

    def get_specification(self, doc_type: str, session_id: Optional[str] = None) -> str:
        """
        Retrieve specific generated specification document (PRD, Architecture, Flow, Tasks, Design).
        """
        doc_key = (doc_type or "").strip().lower()
        target_filename = self.DOC_TYPE_MAPPING.get(doc_key)
        if not target_filename:
            # Check if exact filename given with .md
            if doc_key.endswith(".md"):
                target_filename = doc_type.strip()
            else:
                valid_types = ", ".join(["PRD", "Architecture", "Flow", "Tasks", "Design", "Bundle"])
                return (
                    f"Error: Unknown document type '{doc_type}'. Valid document types are: {valid_types}."
                )

        sid = self.resolve_session_id(session_id)
        if not sid:
            return (
                f"Error: No VoGenFlow session found. Please run a generation or specify an existing session_id."
            )

        artifacts = self.get_session_artifacts(sid)

        # Check direct filename match
        if target_filename in artifacts:
            return artifacts[target_filename]

        # Bidirectional alias resolution between design_proposal.md and design.md
        if target_filename.lower() in ("design_proposal.md", "design.md"):
            alt_key = "design.md" if target_filename.lower() == "design_proposal.md" else "design_proposal.md"
            if alt_key in artifacts:
                return artifacts[alt_key]
            for k, v in artifacts.items():
                if k.lower() == alt_key.lower():
                    return v

        # Case-insensitive search across artifact keys
        for k, v in artifacts.items():
            if k.lower() == target_filename.lower():
                return v

        # If missing from artifacts, attempt synthesis via ProjectIR views
        ir, _ = self.get_project_ir(sid)
        if ir:
            if target_filename == "PRD.md":
                return ir.to_prd_markdown()
            elif target_filename == "Architecture.md":
                return ir.to_architecture_markdown()
            elif target_filename == "Flow.md":
                return ir.to_flow_markdown()
            elif target_filename == "tasks.md":
                return ir.to_tasks_markdown()
            elif target_filename in ("design_proposal.md", "design.md"):
                return ir.to_design_markdown()
            elif target_filename == "master_execution_bundle.md":
                return (
                    f"# Master Execution Bundle: {ir.project_name}\n\n"
                    f"---\n\n{ir.to_prd_markdown()}\n\n"
                    f"---\n\n{ir.to_architecture_markdown()}\n\n"
                    f"---\n\n{ir.to_flow_markdown()}\n\n"
                    f"---\n\n{ir.to_tasks_markdown()}\n\n"
                    f"---\n\n{ir.to_design_markdown()}"
                )

        available = list(artifacts.keys()) if artifacts else "None"
        return (
            f"Error: Specification '{target_filename}' not found for session '{sid}'. "
            f"Available artifacts: {available}."
        )

    def get_ddl(self, session_id: Optional[str] = None) -> str:
        """
        Extract raw executable SQL DDL schema from the architecture specification.
        """
        sid = self.resolve_session_id(session_id)
        if not sid:
            return "-- Error: No VoGenFlow session found. Please specify a valid session_id."

        # 1. Try canonical ProjectIR
        ir, _ = self.get_project_ir(sid)
        if ir and ir.architecture and ir.architecture.database_ddl:
            ddl = ir.architecture.database_ddl.strip()
            # If DDL is wrapped in ```sql, clean it
            ddl = re.sub(r"^```sql\s*", "", ddl, flags=re.IGNORECASE)
            ddl = re.sub(r"\s*```$", "", ddl)
            if ddl:
                return ddl

        # 2. Extract from Architecture.md artifact
        artifacts = self.get_session_artifacts(sid)
        arch_text = artifacts.get("Architecture.md") or artifacts.get("architecture.md") or ""

        if arch_text:
            # Match ```sql blocks, handling unclosed blocks at EOF or header
            match = re.search(r"```sql(?:\s*\w+)?\r?\n([\s\S]*?)(?:```|\Z)", arch_text, re.IGNORECASE)
            if match:
                raw_sql = match.group(1).strip()
                # Stop if it runs into another markdown header
                header_match = re.search(r"\n##+\s+", raw_sql)
                if header_match:
                    raw_sql = raw_sql[:header_match.start()].strip()
                if raw_sql:
                    return raw_sql

        return (
            f"-- Error: No SQL DDL found in architecture specification for session '{sid}'.\n"
            f"-- Ensure the council deliberation completed the system architecture stage."
        )

    def get_tasks(self, session_id: Optional[str] = None, format: str = "json") -> str:
        """
        Return structured, phased implementation task breakdown in JSON or Markdown.
        """
        sid = self.resolve_session_id(session_id)
        if not sid:
            err = {"error": "No session found", "status": "not_found"}
            return json.dumps(err, indent=2) if format.lower() == "json" else "Error: No session found."

        ir, _ = self.get_project_ir(sid)
        artifacts = self.get_session_artifacts(sid)

        # Output Markdown directly if requested
        if format.lower() == "markdown":
            if ir:
                return ir.to_tasks_markdown()
            tasks_md = artifacts.get("tasks.md") or artifacts.get("tasks")
            if tasks_md:
                return tasks_md
            return f"Error: No tasks found for session '{sid}'."

        # Otherwise format as structured JSON
        if ir and ir.tasks:
            milestones = []
            for m in ir.tasks:
                task_items = [
                    {
                        "description": t.description,
                        "file_target": t.file_target,
                        "verification_command": t.verification_command,
                    }
                    for t in m.tasks
                ]
                milestones.append({
                    "milestone_id": m.milestone_id,
                    "title": m.title,
                    "tasks": task_items,
                })

            result = {
                "session_id": sid,
                "project_name": ir.project_name,
                "milestones": milestones,
                "total_milestones": len(milestones),
                "total_tasks": sum(len(m["tasks"]) for m in milestones),
            }
            return json.dumps(result, indent=2)

        # Fallback: Parse tasks.md into structured JSON
        tasks_text = artifacts.get("tasks.md") or ""
        if tasks_text:
            milestones = []
            current_ms = None
            for line in tasks_text.splitlines():
                ms_match = re.match(r"^##\s+(?:Milestone\s+)?([A-Za-z0-9_\-]+)\s*[:\-—]?\s*(.*)", line)
                if ms_match:
                    current_ms = {
                        "milestone_id": ms_match.group(1).strip(),
                        "title": ms_match.group(2).strip() or ms_match.group(1).strip(),
                        "tasks": [],
                    }
                    milestones.append(current_ms)
                    continue

                task_match = re.match(r"^-\s*\[[ x]\]\s*(.+)", line)
                if task_match:
                    desc = task_match.group(1).strip()
                    file_target = None
                    file_match = re.search(r"`([^`]+(\.[a-zA-Z0-9]+))`", desc)
                    if file_match:
                        file_target = file_match.group(1)

                    if current_ms is None:
                        current_ms = {
                            "milestone_id": "M1",
                            "title": "Phase 1: Implementation Tasks",
                            "tasks": [],
                        }
                        milestones.append(current_ms)

                    current_ms["tasks"].append({
                        "description": desc,
                        "file_target": file_target,
                        "verification_command": None,
                    })

            result = {
                "session_id": sid,
                "project_name": "VoGenFlow Engineered System",
                "milestones": milestones,
                "total_milestones": len(milestones),
                "total_tasks": sum(len(m["tasks"]) for m in milestones),
            }
            return json.dumps(result, indent=2)

        return json.dumps({
            "session_id": sid,
            "error": "No tasks found in session specifications",
            "milestones": [],
        }, indent=2)

    def query_architecture(
        self,
        query: str,
        session_id: Optional[str] = None,
        top_k: int = 3,
    ) -> Dict[str, Any]:
        """
        Run semantic search and advisory lookup across grounded knowledge base and session specs.
        """
        top_k = max(0, min(int(top_k), 50))
        clean_query = (query or "").strip()
        if not clean_query:
            return {"error": "Query parameter cannot be empty", "matches": []}

        # 1. Search Curated Knowledge Catalog
        catalog_matches = self.knowledge_db.search(clean_query, top_k=top_k)

        # 2. Search Active Session Specifications
        session_matches = []
        sid = self.resolve_session_id(session_id)
        if sid:
            artifacts = self.get_session_artifacts(sid)
            q_terms = [t for t in re.sub(r"[^\w\s]", " ", clean_query.lower()).split() if len(t) > 2]
            for doc_name, content in artifacts.items():
                paragraphs = [p.strip() for p in content.split("\n\n") if len(p.strip()) > 30]
                for p in paragraphs:
                    p_lower = p.lower()
                    score = sum(1 for term in q_terms if term in p_lower)
                    if score > 0:
                        session_matches.append({
                            "session_id": sid,
                            "source_doc": doc_name,
                            "snippet": p[:400] + ("..." if len(p) > 400 else ""),
                            "match_score": score,
                        })

            session_matches.sort(key=lambda x: x["match_score"], reverse=True)
            session_matches = session_matches[:top_k]

        # 3. Formulate architectural recommendation
        advisory = (
            f"Grounding Architecture Search for '{clean_query}'. "
            f"Found {len(catalog_matches)} matching curated engineering blueprints and "
            f"{len(session_matches)} relevant sections in session '{sid or 'none'}'. "
            f"Ensure all database changes respect Row-Level Security (RLS), multi-tenant isolation, "
            f"and strict typed contracts."
        )

        return {
            "query": clean_query,
            "session_id": sid,
            "advisory": advisory,
            "catalog_templates": [
                {
                    "title": t.get("title"),
                    "category": t.get("category"),
                    "description": t.get("description"),
                    "keywords": t.get("keywords", []),
                    "snippet": t.get("snippet", ""),
                    "relevance_score": t.get("relevance_score", 0.0),
                }
                for t in catalog_matches
            ],
            "session_matches": session_matches,
        }


# --- FastMCP Server Instance ---

mcp = FastMCP(
    name="VoGenFlow",
    instructions=(
        "VoGenFlow Model Context Protocol (MCP) Server. "
        "Provides downstream coding agents (Cursor, Claude Code, Antigravity) with programmatic "
        "access to Canonical ProjectIR, specifications (PRD, Architecture, Flow, Tasks, Design), "
        "production PostgreSQL/Supabase SQL DDL, actionable task breakdowns, and grounded architecture knowledge."
    ),
)

# Global Resolver Instance
resolver = VoGenFlowResolver()


# --- FastMCP Tool Definitions ---

@mcp.tool(
    name="vogenflow_get_project_ir",
    description=(
        "Returns the complete Canonical ProjectIR JSON for a session/project. "
        "Downstream agents can inspect requirements, architecture, API contracts, data models, and non-functional SLAs."
    ),
)
def vogenflow_get_project_ir(session_id: Optional[str] = None) -> str:
    """Fetch Canonical ProjectIR as formatted JSON for a given session or latest session."""
    try:
        ir, sid = resolver.get_project_ir(session_id)
        if not ir:
            available = [s["session_id"] for s in resolver.list_sessions(limit=5)]
            return json.dumps({
                "status": "error",
                "message": f"ProjectIR not found for session '{session_id or 'latest'}'.",
                "available_sessions": available,
            }, indent=2)
        return ir.model_dump_json(indent=2)
    except Exception as e:
        logger.error("vogenflow_get_project_ir error: %s", e)
        return json.dumps({"status": "error", "message": str(e)}, indent=2)


@mcp.tool(
    name="vogenflow_get_specification",
    description=(
        "Returns specific generated documents (PRD, Architecture, Flow, Tasks, Design, Bundle) by type "
        "for a given session or latest session."
    ),
)
def vogenflow_get_specification(doc_type: str, session_id: Optional[str] = None) -> str:
    """Fetch specific generated specification document (PRD, Architecture, Flow, Tasks, Design)."""
    try:
        return resolver.get_specification(doc_type=doc_type, session_id=session_id)
    except Exception as e:
        logger.error("vogenflow_get_specification error: %s", e)
        return f"Error retrieving specification '{doc_type}': {str(e)}"


@mcp.tool(
    name="vogenflow_get_ddl",
    description=(
        "Returns raw executable SQL/PostgreSQL/Supabase DDL schemas synthesized from the architecture, "
        "ready for database migration."
    ),
)
def vogenflow_get_ddl(session_id: Optional[str] = None) -> str:
    """Extract raw executable SQL DDL schema for database provisioning."""
    try:
        return resolver.get_ddl(session_id=session_id)
    except Exception as e:
        logger.error("vogenflow_get_ddl error: %s", e)
        return f"-- Error extracting SQL DDL: {str(e)}"


@mcp.tool(
    name="vogenflow_get_tasks",
    description=(
        "Returns structured, phased implementation task breakdown. "
        "Format can be 'json' (structured milestones & tasks) or 'markdown' (actionable checklist)."
    ),
)
def vogenflow_get_tasks(session_id: Optional[str] = None, format: str = "json") -> str:
    """Return implementation task roadmap in JSON or Markdown."""
    try:
        return resolver.get_tasks(session_id=session_id, format=format)
    except Exception as e:
        logger.error("vogenflow_get_tasks error: %s", e)
        if format.lower() == "json":
            return json.dumps({"status": "error", "message": str(e)}, indent=2)
        return f"Error retrieving tasks: {str(e)}"


@mcp.tool(
    name="vogenflow_query_architecture",
    description=(
        "Runs semantic search or advisory lookup across the grounded knowledge base, "
        "architectural templates, and current session specifications."
    ),
)
def vogenflow_query_architecture(
    query: str,
    session_id: Optional[str] = None,
    top_k: int = 3,
) -> str:
    """Query architectural blueprints, patterns, and session specs."""
    try:
        top_k = max(0, min(int(top_k), 50))
        res = resolver.query_architecture(query=query, session_id=session_id, top_k=top_k)
        return json.dumps(res, indent=2)
    except Exception as e:
        logger.error("vogenflow_query_architecture error: %s", e)
        return json.dumps({"status": "error", "message": str(e)}, indent=2)


@mcp.tool(
    name="vogenflow_list_sessions",
    description="Lists all available VoGenFlow sessions with metadata and timestamps.",
)
def vogenflow_list_sessions(limit: int = 20) -> str:
    """List all available sessions in VoGenFlow."""
    try:
        limit = max(0, min(int(limit), 500))
        sessions = resolver.list_sessions(limit=limit)
        return json.dumps({"total": len(sessions), "sessions": sessions}, indent=2)
    except Exception as e:
        logger.error("vogenflow_list_sessions error: %s", e)
        return json.dumps({"status": "error", "message": str(e)}, indent=2)


# --- FastMCP Resources ---

@mcp.resource("vogenflow://session/{session_id}/project_ir")
def get_session_project_ir_resource(session_id: str) -> str:
    """Returns canonical ProjectIR JSON for the specified session_id."""
    try:
        ir, sid = resolver.get_project_ir(session_id)
        if not ir:
            return json.dumps({"error": f"ProjectIR not found for session '{session_id}'"}, indent=2)
        return ir.model_dump_json(indent=2)
    except (ValueError, Exception) as exc:
        return json.dumps({"error": f"Invalid session or retrieval failure for '{session_id}': {exc}"}, indent=2)


@mcp.resource("vogenflow://session/{session_id}/specs")
def get_session_specs_resource(session_id: str) -> str:
    """Returns bundled markdown specifications for the specified session_id."""
    try:
        sid = resolver.resolve_session_id(session_id)
        if not sid:
            return f"# Error\n\nSession '{session_id}' not found."

        artifacts = resolver.get_session_artifacts(sid)
        if not artifacts:
            # Fallback to ProjectIR views
            ir, _ = resolver.get_project_ir(sid)
            if ir:
                return (
                    f"# Specifications Bundle: {ir.project_name}\n\n"
                    f"---\n\n{ir.to_prd_markdown()}\n\n"
                    f"---\n\n{ir.to_architecture_markdown()}\n\n"
                    f"---\n\n{ir.to_flow_markdown()}\n\n"
                    f"---\n\n{ir.to_tasks_markdown()}\n\n"
                    f"---\n\n{ir.to_design_markdown()}"
                )
            return f"# Error\n\nNo specifications found for session '{sid}'."

        bundle_parts = [f"# VoGenFlow Specifications Bundle: Session {sid}\n"]
        for name, content in artifacts.items():
            bundle_parts.append(f"\n\n<!-- === FILE: {name} === -->\n\n{content}")
        return "\n".join(bundle_parts)
    except (ValueError, Exception) as exc:
        return f"# Error\n\nInvalid session or retrieval failure for '{session_id}': {exc}"


@mcp.resource("vogenflow://sessions")
def get_sessions_resource() -> str:
    """Returns JSON listing of all available sessions."""
    sessions = resolver.list_sessions(limit=50)
    return json.dumps({"sessions": sessions}, indent=2)


# --- Standalone CLI Entrypoint ---

def main():
    """CLI entry point for running the MCP server over stdio or SSE."""
    import argparse
    parser = argparse.ArgumentParser(description="VoGenFlow MCP Server")
    parser.add_argument(
        "--transport",
        default="stdio",
        choices=["stdio", "sse", "streamable-http"],
        help="Transport protocol (default: stdio)",
    )
    args = parser.parse_args()

    if args.transport == "stdio":
        mcp.run(transport="stdio")
    else:
        mcp.run(transport=args.transport)


if __name__ == "__main__":
    main()
