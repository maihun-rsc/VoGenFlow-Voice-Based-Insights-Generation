"""
tests/test_mcp_e2e.py
End-to-End Stdio Subprocess Test Suite for VoGenFlow MCP Server.

Validates that external MCP clients (Cursor, Claude Code, Antigravity)
can spawn the server as a real OS subprocess communicating over stdio JSON-RPC streams,
execute all 6 FastMCP tools, query all 3 URI resources, and gracefully handle edge cases.
"""

import os
import sys
import json
import asyncio
import tempfile
from pathlib import Path
import pytest

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from src.db.sqlite_store import SQLiteStore
from src.models.project_ir import create_project_ir_from_council_artifacts

REPO_ROOT = Path(__file__).resolve().parent.parent

# Sample rich artifacts for seeding test sessions
MOCK_PRD = """# Product Requirements Document (PRD) // VoGenFlow
## 1. Executive Summary & Problem Statement
VoGenFlow transforms spontaneous spoken architecture brainstorms into formal specifications.

## 2. Target Personas
### Lead Systems Architect
- Role: Designs distributed backends and database schemas.
- Pain Points: Manual documentation overhead and drift.
- Needs: Executable DDL, sequence diagrams, and task milestones.

## 3. Detailed Functional Requirements
### REQ-001 [P0]: High-Throughput Event Streaming
- Priority: P0
- Acceptance Criteria:
  - Process at least 10,000 events/second
  - Zero message loss under partition

## 4. Non-Functional SLAs Table
| Metric | Target | Verification Method |
|---|---|---|
| P95 Ingress Latency | < 30ms | Load testing |
| Availability | 99.99% | Chaos simulation |

## 5. STRIDE Security Threat Matrix
| Category | Threat Description | Mitigation |
|---|---|---|
| Spoofing | Unauthorized client access | JWT authentication with Ed25519 |
| Tampering | SQL injection in parameters | Parameterized queries and RLS |
"""

MOCK_ARCH = """# Architecture Specification // VoGenFlow
```mermaid
flowchart TD
    Client[Client App] --> Ingress[FastAPI Gateway]
    Ingress --> DB[(PostgreSQL 16)]
```

### PostgreSQL DDL Schema
```sql
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

CREATE TABLE accounts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id VARCHAR(64) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE accounts ENABLE ROW LEVEL SECURITY;

CREATE POLICY accounts_tenant_isolation ON accounts
    FOR ALL
    USING (tenant_id = current_setting('app.current_tenant', true));
```
"""

MOCK_FLOW = """# Systems Lifecycle & Sequence Flow
```mermaid
sequenceDiagram
    autonumber
    Client->>Gateway: POST /api/deliberate
    Gateway->>DB: Persist Session
    Gateway-->>Client: 200 OK (Artifacts Bundle)
```
"""

MOCK_TASKS = """# Phased Delivery Roadmap
## Milestone 1: Data Models & Persistence
- [x] Schema DDL creation
- [ ] Database connection pool setup

## Milestone 2: Service Ingress Gateway
- [ ] WebSocket streaming endpoint
- [ ] Authentication middleware
"""

MOCK_DESIGN_PROPOSAL = """# UI/UX Specification: Monolith Luxury Reductionist
## Design Tokens
- Onyx Black: `#000000`
- Vellum Light: `#F7F6F2`
- Brushed Gold: `#D4AF37`
"""

MOCK_DESIGN_ALT = """# Design Specification: Vellum Theme
- Primary Background: `#F7F6F2`
- Accent: `#D4AF37`
"""


def run_coro(coro):
    """Run an async coroutine synchronously."""
    return asyncio.run(coro)


@pytest.fixture(scope="module")
def seeded_env():
    """Create isolated SQLite database with seeded sessions and return environment dictionary."""
    temp_dir = tempfile.TemporaryDirectory()
    db_file = Path(temp_dir.name) / "test_mcp_e2e.db"
    store = SQLiteStore(db_path=db_file)

    # 1. Seed primary session
    session_id_1 = "e2e_session_primary"
    artifacts_1 = {
        "PRD.md": MOCK_PRD,
        "Architecture.md": MOCK_ARCH,
        "Flow.md": MOCK_FLOW,
        "tasks.md": MOCK_TASKS,
        "design_proposal.md": MOCK_DESIGN_PROPOSAL,
    }
    ir_1 = create_project_ir_from_council_artifacts("VoGenFlow E2E Test Project", artifacts_1)
    store.save_session(
        session_id=session_id_1,
        project_id="proj_e2e_test",
        status="completed",
        metadata={"environment": "e2e_test", "tier": "subprocess"},
        artifacts=artifacts_1,
        project_ir=ir_1,
    )

    # 2. Seed secondary session with design.md (testing bidirectional alias resolution)
    session_id_2 = "e2e_session_alt_design"
    artifacts_2 = {
        "PRD.md": MOCK_PRD,
        "design.md": MOCK_DESIGN_ALT,
    }
    store.save_session(
        session_id=session_id_2,
        project_id="proj_e2e_alt",
        status="completed",
        metadata={"test": "bidirectional_design"},
        artifacts=artifacts_2,
    )

    env = os.environ.copy()
    env["PYTHONPATH"] = str(REPO_ROOT)
    env["VOGENFLOW_DB_PATH"] = str(db_file)
    env["VOGENFLOW_OFFLINE_MODE"] = "1"

    yield {
        "env": env,
        "db_path": db_file,
        "session_1": session_id_1,
        "session_2": session_id_2,
    }

    store.close()
    temp_dir.cleanup()


class TestMCPServerSubprocessE2E:
    """End-to-end stdio subprocess test suite verifying real MCP client/server interaction."""

    def test_mcp_server_handshake_and_capabilities(self, seeded_env):
        """Verify process spawn, stdio JSON-RPC handshake, and capability advertisement."""
        async def _test():
            server_params = StdioServerParameters(
                command=sys.executable,
                args=["-m", "src.mcp.server", "--transport", "stdio"],
                env=seeded_env["env"],
            )

            async with stdio_client(server_params) as (read_stream, write_stream):
                async with ClientSession(read_stream, write_stream) as session:
                    init_result = await session.initialize()
                    assert init_result is not None
                    assert init_result.serverInfo.name == "VoGenFlow"

                    tools_res = await session.list_tools()
                    tool_names = [t.name for t in tools_res.tools]
                    expected_tools = [
                        "vogenflow_get_project_ir",
                        "vogenflow_get_specification",
                        "vogenflow_get_ddl",
                        "vogenflow_get_tasks",
                        "vogenflow_query_architecture",
                        "vogenflow_list_sessions",
                    ]
                    for exp in expected_tools:
                        assert exp in tool_names, f"Tool {exp} missing from advertised tools"

                    res_res = await session.list_resources()
                    res_uris = [str(r.uri) for r in res_res.resources]
                    assert "vogenflow://sessions" in res_uris

        run_coro(_test())

    def test_tool_vogenflow_get_project_ir(self, seeded_env):
        """Test Tool 1: vogenflow_get_project_ir with seeded session."""
        async def _test():
            server_params = StdioServerParameters(
                command=sys.executable,
                args=["-m", "src.mcp.server", "--transport", "stdio"],
                env=seeded_env["env"],
            )

            async with stdio_client(server_params) as (read_stream, write_stream):
                async with ClientSession(read_stream, write_stream) as session:
                    await session.initialize()

                    res = await session.call_tool(
                        "vogenflow_get_project_ir",
                        arguments={"session_id": seeded_env["session_1"]},
                    )
                    assert len(res.content) > 0
                    payload = json.loads(res.content[0].text)
                    assert "VoGenFlow" in payload["project_name"]
                    assert "target_personas" in payload
                    assert len(payload["target_personas"]) > 0
                    assert "Lead" in payload["target_personas"][0]["name"]
                    assert "requirements" in payload
                    assert "non_functional_slas" in payload
                    assert "architecture" in payload

        run_coro(_test())

    def test_tool_vogenflow_get_specification(self, seeded_env):
        """Test Tool 2: vogenflow_get_specification for PRD, Architecture, Flow, Tasks, Design, Bundle."""
        async def _test():
            server_params = StdioServerParameters(
                command=sys.executable,
                args=["-m", "src.mcp.server", "--transport", "stdio"],
                env=seeded_env["env"],
            )

            async with stdio_client(server_params) as (read_stream, write_stream):
                async with ClientSession(read_stream, write_stream) as session:
                    await session.initialize()
                    sid = seeded_env["session_1"]

                    # PRD
                    prd_res = await session.call_tool("vogenflow_get_specification", arguments={"doc_type": "prd", "session_id": sid})
                    assert "Product Requirements Document" in prd_res.content[0].text

                    # Architecture
                    arch_res = await session.call_tool("vogenflow_get_specification", arguments={"doc_type": "architecture", "session_id": sid})
                    assert "CREATE TABLE accounts" in arch_res.content[0].text

                    # Flow
                    flow_res = await session.call_tool("vogenflow_get_specification", arguments={"doc_type": "flow", "session_id": sid})
                    assert "sequenceDiagram" in flow_res.content[0].text

                    # Tasks
                    tasks_res = await session.call_tool("vogenflow_get_specification", arguments={"doc_type": "tasks", "session_id": sid})
                    assert "Milestone 1" in tasks_res.content[0].text

                    # Design (design_proposal.md)
                    design_res = await session.call_tool("vogenflow_get_specification", arguments={"doc_type": "design", "session_id": sid})
                    assert "Monolith Luxury" in design_res.content[0].text

                    # Bidirectional test: query "design_proposal.md" on session containing "design.md"
                    alt_sid = seeded_env["session_2"]
                    bidir_res = await session.call_tool("vogenflow_get_specification", arguments={"doc_type": "design_proposal.md", "session_id": alt_sid})
                    assert "Vellum Theme" in bidir_res.content[0].text

                    # Bundle
                    bundle_res = await session.call_tool("vogenflow_get_specification", arguments={"doc_type": "bundle", "session_id": sid})
                    assert "Master Execution Bundle" in bundle_res.content[0].text

        run_coro(_test())

    def test_tool_vogenflow_get_ddl(self, seeded_env):
        """Test Tool 3: vogenflow_get_ddl extracting executable SQL schema."""
        async def _test():
            server_params = StdioServerParameters(
                command=sys.executable,
                args=["-m", "src.mcp.server", "--transport", "stdio"],
                env=seeded_env["env"],
            )

            async with stdio_client(server_params) as (read_stream, write_stream):
                async with ClientSession(read_stream, write_stream) as session:
                    await session.initialize()

                    res = await session.call_tool("vogenflow_get_ddl", arguments={"session_id": seeded_env["session_1"]})
                    sql = res.content[0].text
                    assert "CREATE TABLE accounts" in sql
                    assert "ROW LEVEL SECURITY" in sql

        run_coro(_test())

    def test_tool_vogenflow_get_tasks(self, seeded_env):
        """Test Tool 4: vogenflow_get_tasks format options (json and markdown)."""
        async def _test():
            server_params = StdioServerParameters(
                command=sys.executable,
                args=["-m", "src.mcp.server", "--transport", "stdio"],
                env=seeded_env["env"],
            )

            async with stdio_client(server_params) as (read_stream, write_stream):
                async with ClientSession(read_stream, write_stream) as session:
                    await session.initialize()
                    sid = seeded_env["session_1"]

                    # JSON format
                    json_res = await session.call_tool("vogenflow_get_tasks", arguments={"session_id": sid, "format": "json"})
                    tasks_data = json.loads(json_res.content[0].text)
                    assert "milestones" in tasks_data or "tasks" in tasks_data or isinstance(tasks_data, list)

                    # Markdown format
                    md_res = await session.call_tool("vogenflow_get_tasks", arguments={"session_id": sid, "format": "markdown"})
                    assert "Milestone" in md_res.content[0].text or "- [" in md_res.content[0].text

        run_coro(_test())

    def test_tool_vogenflow_query_architecture(self, seeded_env):
        """Test Tool 5: vogenflow_query_architecture semantic / keyword search."""
        async def _test():
            server_params = StdioServerParameters(
                command=sys.executable,
                args=["-m", "src.mcp.server", "--transport", "stdio"],
                env=seeded_env["env"],
            )

            async with stdio_client(server_params) as (read_stream, write_stream):
                async with ClientSession(read_stream, write_stream) as session:
                    await session.initialize()

                    res = await session.call_tool(
                        "vogenflow_query_architecture",
                        arguments={"query": "PostgreSQL database accounts", "session_id": seeded_env["session_1"], "top_k": 3},
                    )
                    text = res.content[0].text
                    assert "accounts" in text or "Knowledge" in text or "Found" in text

        run_coro(_test())

    def test_tool_vogenflow_list_sessions(self, seeded_env):
        """Test Tool 6: vogenflow_list_sessions returns aggregated session entries."""
        async def _test():
            server_params = StdioServerParameters(
                command=sys.executable,
                args=["-m", "src.mcp.server", "--transport", "stdio"],
                env=seeded_env["env"],
            )

            async with stdio_client(server_params) as (read_stream, write_stream):
                async with ClientSession(read_stream, write_stream) as session:
                    await session.initialize()

                    res = await session.call_tool("vogenflow_list_sessions", arguments={"limit": 10})
                    data = json.loads(res.content[0].text)
                    assert "sessions" in data
                    session_ids = [s["session_id"] for s in data["sessions"]]
                    assert seeded_env["session_1"] in session_ids
                    assert seeded_env["session_2"] in session_ids

        run_coro(_test())

    def test_all_uri_resources(self, seeded_env):
        """Test all 3 FastMCP URI Resources over stdio."""
        async def _test():
            server_params = StdioServerParameters(
                command=sys.executable,
                args=["-m", "src.mcp.server", "--transport", "stdio"],
                env=seeded_env["env"],
            )

            async with stdio_client(server_params) as (read_stream, write_stream):
                async with ClientSession(read_stream, write_stream) as session:
                    await session.initialize()
                    sid = seeded_env["session_1"]

                    # Resource 1: ProjectIR JSON
                    uri_ir = f"vogenflow://session/{sid}/project_ir"
                    res_ir = await session.read_resource(uri_ir)
                    assert len(res_ir.contents) > 0
                    ir_data = json.loads(res_ir.contents[0].text)
                    assert "VoGenFlow" in ir_data["project_name"]

                    # Resource 2: Bundled Specifications
                    uri_specs = f"vogenflow://session/{sid}/specs"
                    res_specs = await session.read_resource(uri_specs)
                    assert len(res_specs.contents) > 0
                    specs_text = res_specs.contents[0].text
                    assert "PRD.md" in specs_text or "VoGenFlow" in specs_text

                    # Resource 3: All Sessions list
                    uri_sessions = "vogenflow://sessions"
                    res_sess = await session.read_resource(uri_sessions)
                    assert len(res_sess.contents) > 0
                    sess_data = json.loads(res_sess.contents[0].text)
                    assert "sessions" in sess_data
                    listed_sids = [s["session_id"] for s in sess_data["sessions"]]
                    assert sid in listed_sids

        run_coro(_test())

    def test_error_and_edge_cases(self, seeded_env):
        """Test edge cases: nonexistent session, invalid session formatting, unknown doc types."""
        async def _test():
            server_params = StdioServerParameters(
                command=sys.executable,
                args=["-m", "src.mcp.server", "--transport", "stdio"],
                env=seeded_env["env"],
            )

            async with stdio_client(server_params) as (read_stream, write_stream):
                async with ClientSession(read_stream, write_stream) as session:
                    await session.initialize()

                    # 1. Non-existent session for tool
                    res_nonexistent = await session.call_tool(
                        "vogenflow_get_project_ir",
                        arguments={"session_id": "nonexistent_sess_999999"},
                    )
                    assert "Error" in res_nonexistent.content[0].text or "not found" in res_nonexistent.content[0].text

                    # 2. Unknown document type
                    res_bad_doc = await session.call_tool(
                        "vogenflow_get_specification",
                        arguments={"doc_type": "invalid_blueprint_type", "session_id": seeded_env["session_1"]},
                    )
                    assert "Error: Unknown document type" in res_bad_doc.content[0].text

                    # 3. Invalid session format in tool
                    res_bad_format = await session.call_tool(
                        "vogenflow_get_project_ir",
                        arguments={"session_id": "bad/id!with$special"},
                    )
                    assert "error" in res_bad_format.content[0].text.lower()

                    # 4. Non-existent session in resource
                    res_res_nonexistent = await session.read_resource("vogenflow://session/nonexistent_sess_999999/project_ir")
                    bad_ir = json.loads(res_res_nonexistent.contents[0].text)
                    assert "error" in bad_ir

                    # 5. Invalid session formatting in resource (handled cleanly without crash)
                    res_res_invalid = await session.read_resource("vogenflow://session/invalid!bad/specs")
                    assert "Error" in res_res_invalid.contents[0].text

        run_coro(_test())
