"""
tests/test_mcp_server.py
Comprehensive Unit and Integration Test Suite for VoGenFlow MCP Server.

Validates:
- FastMCP tool registration and metadata
- FastMCP resource template registration
- Direct function invocation and async protocol call_tool invocation
- Canonical ProjectIR JSON serialization and rehydration
- Multi-document specification retrieval (PRD, Architecture, Flow, Tasks, Design)
- Raw executable SQL DDL extraction
- Structured phased task roadmap generation (JSON and Markdown)
- Semantic architectural query across curated catalog and session artifacts
- MCP Resource reading (vogenflow://session/{id}/project_ir, vogenflow://session/{id}/specs)
- Security path traversal guards and edge-case error handling
"""

import os
import sys
import json
import uuid
import pytest
import asyncio
from pathlib import Path
from typing import Dict, Any

from mcp.server.fastmcp import FastMCP
from src.mcp.server import (
    mcp,
    resolver,
    VoGenFlowResolver,
    vogenflow_get_project_ir,
    vogenflow_get_specification,
    vogenflow_get_ddl,
    vogenflow_get_tasks,
    vogenflow_query_architecture,
    vogenflow_list_sessions,
    get_session_project_ir_resource,
    get_session_specs_resource,
    get_sessions_resource,
    main,
)
from src.models.project_ir import (
    ProjectIR,
    ArchitectureSpec,
    LifecycleSpec,
    Requirement,
    TaskMilestone,
    TaskItem,
)
from src.db.sqlite_store import SQLiteStore


@pytest.fixture(scope="module")
def sample_session_id(tmp_path_factory) -> str:
    """Fixture providing an ephemeral, fully-populated test session."""
    test_sid = f"test_mcp_{uuid.uuid4().hex[:8]}"
    base_dir = tmp_path_factory.mktemp("mcp_test_env")
    output_dir = base_dir / "output"
    sessions_dir = output_dir / "sessions" / test_sid
    sessions_dir.mkdir(parents=True, exist_ok=True)

    # 1. Populate markdown artifacts on disk
    prd_content = (
        f"# Product Requirements Document: Test VoGenFlow SaaS\n\n"
        f"### Executive Summary\n"
        f"A cloud-native real-time acoustic pipeline with strict RLS.\n\n"
        f"### [P0] REQ-001: Audio Ingestion\n"
        f"As an engineer I want 16kHz audio ingestion so that latency is under 200ms.\n"
        f"- [ ] Ingestion endpoint operational\n\n"
        f"### [P0] REQ-002: Tenant Isolation\n"
        f"As a compliance officer I need strict Row-Level Security.\n"
        f"- [ ] RLS policies verified\n"
    )
    arch_content = (
        f"# System Architecture Specification: Test VoGenFlow SaaS\n\n"
        f"## 1. Overview\n"
        f"Event-driven microservices architecture.\n\n"
        f"## 2. Microservice Topology\n"
        f"```mermaid\nflowchart TD\n  Client --> Gateway\n  Gateway --> DB\n```\n\n"
        f"## 3. Database DDL\n"
        f"```sql\n"
        f"CREATE TABLE IF NOT EXISTS test_users (\n"
        f"    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),\n"
        f"    email TEXT UNIQUE NOT NULL,\n"
        f"    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()\n"
        f");\n"
        f"ALTER TABLE test_users ENABLE ROW LEVEL SECURITY;\n"
        f"```\n"
    )
    flow_content = (
        f"# Systems Lifecycle & Sequence Flow: Test VoGenFlow SaaS\n\n"
        f"```mermaid\nsequenceDiagram\n  Client->>Server: Audio\n  Server-->>Client: Insights\n```\n"
    )
    tasks_content = (
        f"# Implementation Tasks & Delivery Plan: Test VoGenFlow SaaS\n\n"
        f"## M1 — Core Domain Infrastructure\n"
        f"- [ ] Create migrations `migrations/001_initial.sql` (Verify: `psql -f migrations/001_initial.sql`)\n"
        f"- [ ] Implement audio buffer `src/audio.py`\n\n"
        f"## M2 — Gateway & Security\n"
        f"- [ ] Configure RLS policies `src/db/rls.sql`\n"
    )
    design_content = (
        f"# Design System Specification: Test VoGenFlow SaaS\n\n"
        f"## 1. Design Tokens\n"
        f"- **Primary**: `#0A0A0A`\n"
        f"- **Accent**: `#3B82F6`\n"
    )

    (sessions_dir / "PRD.md").write_text(prd_content, encoding="utf-8")
    (sessions_dir / "Architecture.md").write_text(arch_content, encoding="utf-8")
    (sessions_dir / "Flow.md").write_text(flow_content, encoding="utf-8")
    (sessions_dir / "tasks.md").write_text(tasks_content, encoding="utf-8")
    (sessions_dir / "design_proposal.md").write_text(design_content, encoding="utf-8")

    # 2. Also register in the global resolver
    resolver.sessions_dir = output_dir / "sessions"

    # Also register in SQLiteStore if active
    if resolver.store:
        try:
            resolver.store.save_session(test_sid, metadata={"project_name": "Test VoGenFlow SaaS"})
            resolver.store.save_artifacts(test_sid, {
                "PRD.md": prd_content,
                "Architecture.md": arch_content,
                "Flow.md": flow_content,
                "tasks.md": tasks_content,
                "design_proposal.md": design_content,
            })
        except Exception:
            pass

    return test_sid


# ==============================================================================
# 1. TOOL & RESOURCE REGISTRATION TESTS
# ==============================================================================

@pytest.mark.unit
def test_mcp_instance_properties():
    """Verify FastMCP server instance initialization and name."""
    assert isinstance(mcp, FastMCP)
    assert mcp.name == "VoGenFlow"
    assert "Model Context Protocol" in mcp.instructions


@pytest.mark.unit
def test_all_required_tools_registered():
    """Verify that all 5 high-value tools plus helper tools are registered."""
    tool_names = [t.name for t in mcp._tool_manager.list_tools()]
    expected = [
        "vogenflow_get_project_ir",
        "vogenflow_get_specification",
        "vogenflow_get_ddl",
        "vogenflow_get_tasks",
        "vogenflow_query_architecture",
        "vogenflow_list_sessions",
    ]
    for exp in expected:
        assert exp in tool_names, f"Tool '{exp}' is not registered in FastMCP"


@pytest.mark.unit
def test_resource_templates_registered():
    """Verify resource templates for project_ir, specs, and sessions are declared."""
    templates = [t.uri_template for t in mcp._resource_manager.list_templates()]
    expected_templates = [
        "vogenflow://session/{session_id}/project_ir",
        "vogenflow://session/{session_id}/specs",
    ]
    for exp in expected_templates:
        assert exp in templates, f"Resource template '{exp}' is not registered"


# ==============================================================================
# 2. DIRECT FUNCTION INVOCATION TESTS
# ==============================================================================

@pytest.mark.unit
def test_vogenflow_get_project_ir_direct(sample_session_id):
    """Test vogenflow_get_project_ir returns valid, parseable ProjectIR JSON."""
    raw_json = vogenflow_get_project_ir(sample_session_id)
    assert isinstance(raw_json, str)
    data = json.loads(raw_json)
    assert "project_name" in data
    assert "architecture" in data
    assert "requirements" in data
    assert len(data["requirements"]) >= 1


@pytest.mark.unit
def test_vogenflow_get_project_ir_nonexistent():
    """Test get_project_ir with a non-existent session handles error gracefully."""
    raw_json = vogenflow_get_project_ir("non_existent_session_999999")
    data = json.loads(raw_json)
    assert data.get("status") == "error"
    assert "not found" in data.get("message", "").lower()


@pytest.mark.unit
def test_vogenflow_get_specification_all_types(sample_session_id):
    """Test retrieving each document specification type."""
    specs = ["PRD", "Architecture", "Flow", "Tasks", "Design"]
    for spec in specs:
        doc = vogenflow_get_specification(doc_type=spec, session_id=sample_session_id)
        assert isinstance(doc, str)
        assert not doc.startswith("Error:"), f"Failed to get {spec}: {doc}"
        assert len(doc) > 30, f"Specification {spec} content too short: {doc}"


@pytest.mark.unit
def test_vogenflow_get_specification_case_insensitivity(sample_session_id):
    """Test case insensitivity and aliases for doc_type."""
    doc_lower = vogenflow_get_specification("prd", session_id=sample_session_id)
    doc_upper = vogenflow_get_specification("PRD.MD", session_id=sample_session_id)
    assert "Product Requirements Document" in doc_lower
    assert "Product Requirements Document" in doc_upper


@pytest.mark.unit
def test_vogenflow_get_specification_invalid_type(sample_session_id):
    """Test invalid doc_type returns an informative error listing valid types."""
    res = vogenflow_get_specification("invalid_unknown_doc", session_id=sample_session_id)
    assert "Error: Unknown document type" in res
    assert "PRD" in res
    assert "Architecture" in res


@pytest.mark.unit
def test_vogenflow_get_ddl_direct(sample_session_id):
    """Test extracting clean executable SQL DDL."""
    ddl = vogenflow_get_ddl(sample_session_id)
    assert isinstance(ddl, str)
    assert not ddl.startswith("-- Error:")
    assert "CREATE TABLE" in ddl
    assert "test_users" in ddl
    assert "ROW LEVEL SECURITY" in ddl
    # Ensure markdown backticks were stripped
    assert "```sql" not in ddl
    assert "```" not in ddl


@pytest.mark.unit
def test_vogenflow_get_ddl_nonexistent():
    """Test DDL extraction on missing session."""
    ddl = vogenflow_get_ddl("non_existent_session_999999")
    assert ddl.startswith("-- Error:")


@pytest.mark.unit
def test_vogenflow_get_tasks_json(sample_session_id):
    """Test tasks output formatted as structured JSON."""
    tasks_raw = vogenflow_get_tasks(session_id=sample_session_id, format="json")
    data = json.loads(tasks_raw)
    assert "session_id" in data
    assert "milestones" in data
    assert len(data["milestones"]) >= 1
    m1 = data["milestones"][0]
    assert "milestone_id" in m1
    assert "tasks" in m1
    assert len(m1["tasks"]) >= 1


@pytest.mark.unit
def test_vogenflow_get_tasks_markdown(sample_session_id):
    """Test tasks output formatted as Markdown checklist."""
    tasks_md = vogenflow_get_tasks(session_id=sample_session_id, format="markdown")
    assert isinstance(tasks_md, str)
    assert "Implementation Tasks" in tasks_md
    assert "- [ ]" in tasks_md


@pytest.mark.unit
def test_vogenflow_query_architecture_direct(sample_session_id):
    """Test semantic query across curated catalog and session artifacts."""
    res_raw = vogenflow_query_architecture(
        query="PostgreSQL Row-Level Security multi-tenant",
        session_id=sample_session_id,
        top_k=2,
    )
    data = json.loads(res_raw)
    assert data["query"] == "PostgreSQL Row-Level Security multi-tenant"
    assert "advisory" in data
    assert "catalog_templates" in data
    assert len(data["catalog_templates"]) > 0
    top_tmpl = data["catalog_templates"][0]
    assert "title" in top_tmpl
    assert "snippet" in top_tmpl


@pytest.mark.unit
def test_vogenflow_list_sessions_direct(sample_session_id):
    """Test session listing."""
    res_raw = vogenflow_list_sessions(limit=10)
    data = json.loads(res_raw)
    assert "total" in data
    assert "sessions" in data
    sids = [s["session_id"] for s in data["sessions"]]
    assert sample_session_id in sids


# ==============================================================================
# 3. ASYNC MCP PROTOCOL CALL_TOOL TESTS
# ==============================================================================

@pytest.mark.unit
def test_async_call_tool_project_ir(sample_session_id):
    """Test calling vogenflow_get_project_ir via FastMCP protocol invocation."""
    async def _run():
        result = await mcp.call_tool("vogenflow_get_project_ir", {"session_id": sample_session_id})
        assert isinstance(result, tuple)
        content_list = result[0]
        assert len(content_list) > 0
        text_content = content_list[0].text
        data = json.loads(text_content)
        assert "project_name" in data

    asyncio.run(_run())


@pytest.mark.unit
def test_async_call_tool_specification(sample_session_id):
    """Test calling vogenflow_get_specification via FastMCP protocol invocation."""
    async def _run():
        result = await mcp.call_tool(
            "vogenflow_get_specification",
            {"doc_type": "Architecture", "session_id": sample_session_id},
        )
        content_list = result[0]
        assert len(content_list) > 0
        text = content_list[0].text
        assert "System Architecture Specification" in text

    asyncio.run(_run())


@pytest.mark.unit
def test_async_call_tool_ddl(sample_session_id):
    """Test calling vogenflow_get_ddl via FastMCP protocol invocation."""
    async def _run():
        result = await mcp.call_tool("vogenflow_get_ddl", {"session_id": sample_session_id})
        content_list = result[0]
        text = content_list[0].text
        assert "CREATE TABLE" in text

    asyncio.run(_run())


@pytest.mark.unit
def test_async_call_tool_tasks(sample_session_id):
    """Test calling vogenflow_get_tasks via FastMCP protocol invocation."""
    async def _run():
        result = await mcp.call_tool(
            "vogenflow_get_tasks",
            {"session_id": sample_session_id, "format": "json"},
        )
        content_list = result[0]
        data = json.loads(content_list[0].text)
        assert "milestones" in data

    asyncio.run(_run())


@pytest.mark.unit
def test_async_call_tool_query_architecture(sample_session_id):
    """Test calling vogenflow_query_architecture via FastMCP protocol invocation."""
    async def _run():
        result = await mcp.call_tool(
            "vogenflow_query_architecture",
            {"query": "real-time WebSocket audio streaming", "session_id": sample_session_id, "top_k": 2},
        )
        content_list = result[0]
        data = json.loads(content_list[0].text)
        assert len(data.get("catalog_templates", [])) > 0

    asyncio.run(_run())


# ==============================================================================
# 4. RESOURCE READING TESTS
# ==============================================================================

@pytest.mark.unit
def test_read_resource_project_ir(sample_session_id):
    """Test reading vogenflow://session/{session_id}/project_ir resource."""
    async def _run():
        uri = f"vogenflow://session/{sample_session_id}/project_ir"
        contents = await mcp.read_resource(uri)
        assert len(contents) > 0
        raw_text = contents[0].content
        data = json.loads(raw_text)
        assert "project_name" in data

    asyncio.run(_run())


@pytest.mark.unit
def test_read_resource_specs(sample_session_id):
    """Test reading vogenflow://session/{session_id}/specs resource."""
    async def _run():
        uri = f"vogenflow://session/{sample_session_id}/specs"
        contents = await mcp.read_resource(uri)
        assert len(contents) > 0
        bundle_text = contents[0].content
        assert "FILE: PRD.md" in bundle_text or "PRD" in bundle_text
        assert "FILE: Architecture.md" in bundle_text or "Architecture" in bundle_text

    asyncio.run(_run())


@pytest.mark.unit
def test_read_resource_sessions_list():
    """Test reading vogenflow://sessions static resource."""
    async def _run():
        uri = "vogenflow://sessions"
        contents = await mcp.read_resource(uri)
        assert len(contents) > 0
        data = json.loads(contents[0].content)
        assert "sessions" in data

    asyncio.run(_run())


# ==============================================================================
# 5. SECURITY & EDGE CASES
# ==============================================================================

@pytest.mark.unit
def test_path_traversal_protection():
    """Verify that malicious directory traversal session IDs are strictly rejected."""
    bad_ids = [
        "../../etc/passwd",
        "..\\..\\windows\\system32",
        "session/../../../secret",
        "invalid!chars@#$",
        "   ",
        "; rm -rf /",
    ]
    for bad_id in bad_ids:
        with pytest.raises(ValueError, match="Invalid session_id"):
            resolver.validate_session_id(bad_id)


@pytest.mark.unit
def test_empty_query_architecture():
    """Verify that empty architectural query returns error structure safely."""
    res_raw = vogenflow_query_architecture(query="   ")
    data = json.loads(res_raw)
    assert "error" in data


@pytest.mark.unit
def test_cli_entrypoint_help(monkeypatch):
    """Verify CLI entry point responds to --help without unhandled exception."""
    test_args = ["server.py", "--help"]
    monkeypatch.setattr(sys, "argv", test_args)
    with pytest.raises(SystemExit) as exc_info:
        main()
    assert exc_info.value.code == 0


@pytest.mark.unit
def test_negative_limit_and_top_k_clamped():
    """Verify negative limit/top_k parameters clamp to 0 instead of slicing backwards."""
    from src.mcp.server import vogenflow_list_sessions

    sessions_data = json.loads(vogenflow_list_sessions(limit=-1))
    assert sessions_data["total"] == 0
    assert sessions_data["sessions"] == []

    arch_data = json.loads(vogenflow_query_architecture(query="PostgreSQL RLS", top_k=-1))
    assert arch_data["catalog_templates"] == []
    assert arch_data["session_matches"] == []
