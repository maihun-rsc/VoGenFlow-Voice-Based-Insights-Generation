# 🏛️ VoGenFlow 2.0: System Architecture Specification (Architecture.md)
> **Document Type:** Production System Architecture & Technical Specifications  
> **Status:** Active & Validated (Anti-Vibe Engineering Standard)  
> **Version:** 2.0.0 Production  
> **Target Topology:** Dual-Target Web SaaS (FastAPI / React 19 / Tailwind v4) & Native Desktop Shell (Tauri v2 / Rust 1.75+)  
> **Target Audience:** Principal Architects, Systems Engineers, Security Auditors & Autonomous Agents  

---

## 📑 Table of Contents
1. [Architectural Vision & Paradigm Shift (Retiring Legacy Monoliths)](#1-architectural-vision--paradigm-shift-retiring-legacy-monoliths)
2. [C4 Container Architecture & Microservice Topologies](#2-c4-container-architecture--microservice-topologies)
3. [Relational Database Architecture & PostgreSQL 16 DDL Contract](#3-relational-database-architecture--postgresql-16-ddl-contract)
4. [Intelligence Core: In-Memory Okapi BM25 RAG & Curated Blueprints](#4-intelligence-core-in-memory-okapi-bm25-rag--curated-blueprints)
5. [The 6-Seat Autonomous Multi-Agent Council DAG](#5-the-6-seat-autonomous-multi-agent-council-dag)
6. [The 4 Enterprise Security Guardrails](#6-the-4-enterprise-security-guardrails)
7. [Master Prompt Compiler & Zero-Shot Intermediate Representation](#7-master-prompt-compiler--zero-shot-intermediate-representation)
8. [Autonomous GitHub PR Dispatcher & Version Control Engine](#8-autonomous-github-pr-dispatcher--version-control-engine)
9. [Concurrency, Threading & Circuit Breaker State Machine](#9-concurrency-threading--circuit-breaker-state-machine)
10. [Interface Contracts & Pydantic API Schemas](#10-interface-contracts--pydantic-api-schemas)

---

## 1. Architectural Vision & Paradigm Shift (Retiring Legacy Monoliths)

### 1.1 The Retirement of the Legacy PyQt6 Desktop Prototype
In early exploration phases (VoGenFlow 1.0), the platform was scaffolded as a monolithic desktop GUI utilizing PyQt6, `QThread` signal loops, and local filesystem paths. While sufficient for initial proof-of-concept audio recording, this architecture presented severe production limitations:
- **Operating System Binding:** Requiring local C++ Qt bindings (`libGL`, `xcb`, PortAudio binary dependencies) created high installation friction and deployment fragility across diverse developer environments.
- **Concurrency & UI Freezes:** Running long-lived multi-agent LLM requests over Qt signals frequently blocked the main UI thread during network latency spikes, degrading rendering frame rates below 30 FPS.
- **Inability to Serve Multi-Device & Cloud Workflows:** A desktop GUI monolith could not support browser-based team collaboration, remote cloud execution, or automated webhook-based CI/CD triggers.

### 1.2 The VoGenFlow 2.0 Dual-Target Topology
VoGenFlow 2.0 completely retires the PyQt6 monolith in favor of an industrial-grade **Dual-Target Decoupled Topology**:
1. **The Core Gateway (FastAPI ASGI):** High-concurrency asynchronous backend handling REST API endpoints, real-time bidirectional WebSocket streaming, non-blocking acoustic buffering, and multi-model routing.
2. **Surface Target A: Cloud Web SaaS:** Built with React 19, modern HTML5 Canvas, Tailwind CSS v4, Lucide Icons, and client-side Mermaid.js rendering. Hosted on zero-cost production cloud tiers (Vercel, Netlify, Fly.io).
3. **Surface Target B: Native Cross-Platform Desktop Shell:** Built on **Tauri v2** using Rust 1.75+. The native Tauri shell compiles down to a lightweight binary (<15MB footprint, <40MB RAM) that bundles the embedded web view with native OS audio driver bridges, completely eliminating heavy Electron or Qt runtimes.

```
+---------------------------------------------------------------------------------------------------------+
|                                    VOGENFLOW 2.0 DUAL-TARGET TOPOLOGY                                   |
+---------------------------------------------------------------------------------------------------------+
|  SURFACE A: BROWSER WEB SAAS                    |  SURFACE B: TAURI V2 DESKTOP SHELL (RUST)             |
|  • React 19 + Tailwind CSS v4                   |  • Rust 1.75+ Native Binary Wrapper (< 15MB)           |
|  • Web Audio API PCM Capture                    |  • Low-level PortAudio / CoreAudio Driver              |
|  • Responsive Viewport Reflow                   |  • Local Air-Gapped Workstation Execution             |
+-------------------------------------------------+-------------------------------------------------------+
                                           │
                                           ▼ (HTTP/2 & WebSockets)
+---------------------------------------------------------------------------------------------------------+
|                                FASTAPI ASGI ASYNCHRONOUS GATEWAY (PORT 8000)                            |
|  • Lifespan Pre-Seeding (Curated DB + Local RAG Engine)                                                  |
|  • WebSocket Audio Stream (/ws/stream) with Real-Time RMS Telemetry                                     |
|  • Quota Management (TrialQuotaManager: 5 Monthly Prompts, 4 Session Edits)                              |
+---------------------------------------------------------------------------------------------------------+
            │                                      │                                      │
            ▼                                      ▼                                      ▼
+-----------------------+              +-----------------------+              +-----------------------+
|  INTELLIGENCE CORE    |              |  6-SEAT COUNCIL DAG   |              |  AUTOMATION PIPELINE  |
|  • Groq Whisper LPU   |              |  • PM Agent (PRD.md)  |              |  • IR Prompt Compiler |
|  • In-Memory BM25 RAG |              |  • 4-Agent Fan-Out    |              |  • Git Branch Engine  |
|  • 4 Security Shields |              |  • Diff Agent Bundler |              |  • gh PR Create Auto  |
+-----------------------+              +-----------------------+              +-----------------------+
```

---

## 2. C4 Container Architecture & Microservice Topologies

The following C4 Container Diagram defines the structural boundaries, protocols, data flows, and runtime responsibilities across VoGenFlow 2.0:

```mermaid
C4Container
    title Container Architecture Diagram: VoGenFlow 2.0 Specification Platform

    Person(developer, "Software Creator / Architect", "Speaks engineering intent into microphone or uploads audio files.")

    System_Boundary(c1, "Presentation Layer (Dual-Target)")
        Container(web_ui, "Web Command Studio", "React 19 / HTML5 / Tailwind v4", "Provides Monolith Luxury interface, orbital council modal, zoomable Mermaid canvas, and audio visualizer.")
        Container(tauri_shell, "Desktop Shell", "Tauri v2 / Rust 1.75+", "Native desktop window hosting Web Studio with native OS audio driver bindings.")
    end

    System_Boundary(c2, "API Gateway & Concurrency Core")
        Container(fastapi_app, "FastAPI ASGI Gateway", "Python 3.10+ / Uvicorn", "Handles routing, session lifecycle, WebSocket audio streaming, and quota limits.")
        Container(ws_endpoint, "WebSocket Streamer", "WebSocket /ws/stream", "Ingests 16kHz PCM chunks, calculates real-time RMS power, and streams telemetry.")
        Container(quota_mgr, "Trial Quota Manager", "In-Memory LRU Cache", "Enforces 5 monthly root prompts and 4 session edits per client IP.")
    end

    System_Boundary(c3, "Intelligence & Grounding Core")
        Container(stt_engine, "STT Service", "Groq Whisper LPU", "Sub-second cloud transcription (<400ms) with segment extraction.")
        Container(rag_engine, "Guarded Local RAG", "In-Memory Okapi BM25", "Scans local code, indexes tokens, enforces 4 security guardrails, grounds prompts.")
        Container(knowledge_db, "Curated Blueprints DB", "In-Memory JSON DB", "Pre-seeds 16 enterprise blueprints (FastAPI, DDL, Supabase, Shadcn).")
    end

    System_Boundary(c4, "Autonomous Council & Model Routing")
        Container(model_router, "Model Router & Circuit Breaker", "Groq SDK / LM Studio Client", "Paces API dispatches, trips circuit on 401, fails over to LM Studio.")
        Container(council_dag, "6-Seat Scatter-Gather DAG", "ThreadPoolExecutor / CAB", "Executes PM, Architect, UI/UX, Systems, Agile, and Diff agents.")
    end

    System_Boundary(c5, "Downstream Execution & Version Control")
        Container(prompt_compiler, "Master Prompt Compiler", "Python IR Compiler", "Compiles 6 artifacts into zero-shot master_execution_bundle.md.")
        Container(pr_dispatcher, "Autonomous PR Dispatcher", "Git / GitHub CLI (gh)", "Provisions feature branch, commits under maihun-rsc, and opens GitHub PR.")
    end

    Rel(developer, web_ui, "Interacts with, records audio, reviews specs", "HTTPS / WSS")
    Rel(developer, tauri_shell, "Launches native workstation application", "OS Native")
    Rel(tauri_shell, web_ui, "Renders UI via Webview2 / WebKit", "IPC")
    Rel(web_ui, ws_endpoint, "Streams raw 16kHz PCM audio frames", "WSS")
    Rel(web_ui, fastapi_app, "Dispatches deliberate, query, and status requests", "JSON / HTTPS")
    Rel(fastapi_app, quota_mgr, "Validates client usage and limits", "Memory")
    Rel(ws_endpoint, stt_engine, "Transcribes buffered WAV audio", "HTTPS / Groq API")
    Rel(fastapi_app, rag_engine, "Indexes codebase and queries context", "Memory")
    Rel(rag_engine, knowledge_db, "Pre-seeds enterprise blueprints", "Memory")
    Rel(fastapi_app, council_dag, "Triggers 3-stage deliberation", "Async / ThreadPool")
    Rel(council_dag, model_router, "Dispatches specialized prompt seat calls", "HTTPS / Socket")
    Rel(council_dag, prompt_compiler, "Sends generated markdown documents", "Memory")
    Rel(prompt_compiler, pr_dispatcher, "Passes compiled bundle and spec suite", "Memory")
    Rel(pr_dispatcher, developer, "Emits live GitHub PR URL or local git instructions", "JSON")
```

---

## 3. Relational Database Architecture & PostgreSQL 16 DDL Contract

When VoGenFlow synthesizes enterprise architectures for cloud backends, it adheres strictly to the **Anti-Vibe Database Standard**:
- **UUIDv7 Primary Keys:** Guarantees cryptographically secure, globally unique, time-ordered identifiers that eliminate B-Tree index fragmentation.
- **Tenant Isolation:** Every table contains an explicit, non-nullable `tenant_id` foreign key.
- **Composite Indexing:** Every multi-tenant table enforces composite indexes on `(tenant_id, created_at DESC)` for sub-millisecond paginated queries.
- **Declarative Row-Level Security (RLS):** 100% data isolation guaranteed at the database engine level via PostgreSQL `USING` and `WITH CHECK` clauses.
- **Soft Deletes & Auditing:** Complete `deleted_at`, `created_at`, and `updated_at` timestamps on all business entities.

### 3.1 Production PostgreSQL 16 DDL Schema

```sql
-- ============================================================================
-- VoGenFlow 2.0 Production Relational Schema & Tenant Isolation DDL
-- Database Engine: PostgreSQL 16+
-- Primary Key Strategy: UUIDv7 (Time-Ordered Sequential UUID)
-- Security: Mandatory Declarative Row-Level Security (RLS)
-- ============================================================================

CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Function to generate UUIDv7 (Unix Timestamp Milliseconds + Random Bits)
CREATE OR REPLACE FUNCTION generate_uuid_v7() 
RETURNS uuid AS $$
DECLARE
    v_time timestamp with time zone := clock_timestamp();
    v_millis bigint := (EXTRACT(epoch FROM v_time) * 1000)::bigint;
    v_bytes bytea;
BEGIN
    v_bytes := set_byte(
        set_byte(
            gen_random_bytes(16),
            6,
            (b'01110000' | (get_byte(gen_random_bytes(1), 0) & 15))::integer
        ),
        8,
        (b'10000000' | (get_byte(gen_random_bytes(1), 0) & 63))::integer
    );
    -- Embed 48-bit timestamp into high-order bytes
    v_bytes := set_byte(v_bytes, 0, ((v_millis >> 40) & 255)::integer);
    v_bytes := set_byte(v_bytes, 1, ((v_millis >> 32) & 255)::integer);
    v_bytes := set_byte(v_bytes, 2, ((v_millis >> 24) & 255)::integer);
    v_bytes := set_byte(v_bytes, 3, ((v_millis >> 16) & 255)::integer);
    v_bytes := set_byte(v_bytes, 4, ((v_millis >> 8) & 255)::integer);
    v_bytes := set_byte(v_bytes, 5, (v_millis & 255)::integer);
    RETURN encode(v_bytes, 'hex')::uuid;
END;
$$ LANGUAGE plpgsql VOLATILE;

-- ----------------------------------------------------------------------------
-- 1. Tenants Table (Organizations / Workspaces)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS tenants (
    id UUID PRIMARY KEY DEFAULT generate_uuid_v7(),
    slug VARCHAR(64) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    plan_tier VARCHAR(32) NOT NULL DEFAULT 'indie' CHECK (plan_tier IN ('indie', 'team', 'enterprise')),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMPTZ NULL
);

CREATE INDEX idx_tenants_slug ON tenants(slug) WHERE deleted_at IS NULL;

-- ----------------------------------------------------------------------------
-- 2. Users Table (Multi-Tenant Members)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT generate_uuid_v7(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    email VARCHAR(255) NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    role VARCHAR(32) NOT NULL DEFAULT 'member' CHECK (role IN ('owner', 'admin', 'member', 'auditor')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMPTZ NULL,
    CONSTRAINT uq_tenant_user_email UNIQUE(tenant_id, email)
);

CREATE INDEX idx_users_tenant_created ON users(tenant_id, created_at DESC) WHERE deleted_at IS NULL;

-- ----------------------------------------------------------------------------
-- 3. Specification Sessions Table
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS specification_sessions (
    id UUID PRIMARY KEY DEFAULT generate_uuid_v7(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    creator_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    title VARCHAR(255) NOT NULL,
    raw_transcript TEXT NOT NULL,
    preset VARCHAR(32) NOT NULL DEFAULT 'standard',
    council_latency_ms INTEGER NOT NULL,
    total_tokens_used INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMPTZ NULL
);

CREATE INDEX idx_sessions_tenant_created ON specification_sessions(tenant_id, created_at DESC) WHERE deleted_at IS NULL;

-- ----------------------------------------------------------------------------
-- 4. Generated Artifacts Table
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS generated_artifacts (
    id UUID PRIMARY KEY DEFAULT generate_uuid_v7(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    session_id UUID NOT NULL REFERENCES specification_sessions(id) ON DELETE CASCADE,
    doc_type VARCHAR(64) NOT NULL CHECK (doc_type IN ('PRD', 'Architecture', 'Flow', 'Design', 'Tasks', 'MasterPrompt')),
    file_path VARCHAR(255) NOT NULL,
    markdown_content TEXT NOT NULL,
    checksum_sha256 CHAR(64) NOT NULL,
    fence_balanced BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMPTZ NULL,
    CONSTRAINT uq_session_doc_type UNIQUE(session_id, doc_type)
);

CREATE INDEX idx_artifacts_tenant_session ON generated_artifacts(tenant_id, session_id);

-- ----------------------------------------------------------------------------
-- 5. Declarative Row-Level Security (RLS) Policies
-- ----------------------------------------------------------------------------
ALTER TABLE tenants ENABLE ROW LEVEL SECURITY;
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE specification_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE generated_artifacts ENABLE ROW LEVEL SECURITY;

-- Tenants Policy (Users can only view their active organization)
CREATE POLICY tenant_isolation_policy ON tenants
    FOR ALL
    USING (id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid);

-- Specification Sessions Policy
CREATE POLICY session_tenant_isolation_policy ON specification_sessions
    FOR ALL
    USING (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid)
    WITH CHECK (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid);

-- Generated Artifacts Policy
CREATE POLICY artifact_tenant_isolation_policy ON generated_artifacts
    FOR ALL
    USING (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid)
    WITH CHECK (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid);
```

---

## 4. Intelligence Core: In-Memory Okapi BM25 RAG & Curated Blueprints

### 4.1 In-Memory Okapi BM25 vs. Heavy Vector Databases
Many modern AI architectures reflexively introduce heavy vector databases (Chroma, Pinecone, Qdrant, Milvus). VoGenFlow 2.0 intentionally implements an **In-Memory Okapi BM25 Retrieval Engine** (`src/rag_engine.py`):
1. **Sub-Millisecond Performance:** Okapi BM25 over in-memory inverted indices delivers query retrieval latencies of **1.25ms** (vs. 40–120ms on vector embedding distance calculations).
2. **Exact Lexical Token Matching:** Software codebases depend on exact symbol precision (e.g., matching exact variable names like `tenant_id`, `CircuitBreaker`, `max_workers`). Dense embeddings frequently conflate structurally distinct tokens due to high cosine proximity.
3. **Zero Deployment Footprint:** Requires zero external Docker containers, zero API calls to embedding providers, zero local GPU VRAM, and runs entirely in 68MB of RAM.

### 4.2 Spoken Query Decomposition & Mathematical BM25 Scoring
Spoken transcripts are conversational and discursive. To ground conversational speech into code tokens, `LocalRAGEngine` executes **Spoken Query Decomposition**:
1. Strips conversational fillers (*"Um, basically, what I want is..."*).
2. Deconstructs the transcript into 2 to 4 discrete architectural sub-queries.
3. Scores chunks across the inverted index using the classical Okapi BM25 formula:

$$\text{Score}(D, Q) = \sum_{i=1}^{N} \text{IDF}(q_i) \cdot \frac{f(q_i, D) \cdot (k_1 + 1)}{f(q_i, D) + k_1 \cdot \left(1 - b + b \cdot \frac{|D|}{\text{avgdl}}\right)}$$

Where:
- $k_1 = 1.5$ (term frequency saturation parameter)
- $b = 0.75$ (document length normalization ratio)
- $\text{IDF}(q_i) = \ln\left(\frac{N - n(q_i) + 0.5}{n(q_i) + 0.5} + 1\right)$

### 4.3 Curated Enterprise Blueprints Pre-Seeding
During the FastAPI server lifespan initialization (`src/api/server.py:lifespan`), `CuratedKnowledgeDB` pre-seeds the RAG engine with 16 enterprise blueprints from `data/curated_knowledge.json`. These blueprints span:
- Multi-tenant FastAPI route handlers with Pydantic validation.
- PostgreSQL 16 DDL with UUIDv7 and RLS schemas.
- Celery / Redis background worker queue patterns.
- Radix UI & Shadcn responsive component layout primitives.
- Microservice Circuit Breaker finite state machines.

---

## 5. The 6-Seat Autonomous Multi-Agent Council DAG

### 5.1 Asynchronous Scatter-Gather DAG Architecture
Monolithic LLM prompt chains suffer from severe quality degradation when tasked with generating multi-faceted engineering specifications. VoGenFlow partitions architectural reasoning into an asynchronous **Scatter-Gather Directed Acyclic Graph (DAG)** (`src/council_engine.py`):

```
+----------------------------------------------------------------------------------------------------+
|                                    3-STAGE SCATTER-GATHER DAG                                      |
+----------------------------------------------------------------------------------------------------+
|                                                                                                    |
|  [Client Voice Input / Transcript]                                                                 |
|         │                                                                                          |
|         ▼                                                                                          |
|  [STAGE 1: PM Lead (pm_agent)] ────────────────────────────────────────────────────────┐           |
|  • Evaluates business problem & personas                                               │           |
|  • Establishes functional requirements (P0/P1/P2) & SLAs                               │           |
|  • Emits: Canonical PRD.md (Frozen Single Source of Truth)                             │           |
|         │                                                                              │           |
|         ▼                                                                              │           |
|  [STAGE 2: Parallel Scatter Fan-Out (ThreadPoolExecutor - max_workers=4)]            │ (Reads)   |
|         ├── [architect_agent] ──► C4 Architecture + PostgreSQL 16 DDL                  │           |
|         ├── [ui_agent]        ──► Monolith Luxury Design Tokens & Viewports             │           |
|         ├── [systems_agent]   ──► Sequence Flows & Failure Recovery Matrices           │           |
|         └── [agile_agent]     ──► Phased Task Checklists & Verification Commands       │           |
|         │                                                                              │           |
|         ▼                                                                              │           |
|  [STAGE 3: Delta Refiner & Bundler (diff_agent)] ◄─────────────────────────────────────┘           |
|  • Validates code fence balancing across all markdown files                                        |
|  • Emits: master_execution_bundle.md & Final Artifact Suite                                        |
|                                                                                                    |
+----------------------------------------------------------------------------------------------------+
```

### 5.2 Council Agent Blackboard (CAB) Thread-Safe Synchronization
To coordinate intermediate findings between agents without blocking or race conditions, the engine utilizes a thread-safe blackboard:
- **Shared In-Memory State:** `council_blackboard = {}` guarded by a re-entrant mutex lock (`threading.Lock`).
- **Canonical PRD Lock:** Once Stage 1 finishes, `PRD.md` is locked. Stage 2 workers access read-only copies of the PRD context, ensuring downstream artifacts cannot diverge from the core product specifications.
- **Progress Event Streaming:** Each seat emits typewriter progress events over WebSockets as tokens stream from the model router.

---

## 6. The 4 Enterprise Security Guardrails

VoGenFlow implements an enterprise defense-in-depth security model across four independent validation layers (`src/rag_engine.py`):

```
+----------------------------------------------------------------------------------------------------+
|                                 THE 4 ENTERPRISE SECURITY GUARDRAILS                               |
+------------------------------------+---------------------------------------------------------------+
| Guardrail Layer                    | Execution Logic & Enforcement Tripwire                        |
+------------------------------------+---------------------------------------------------------------+
| 1. Sensitive File Blocker          | Traverses file paths during indexing; automatically blocks    |
|    (Data Loss Prevention)          | 14 secret patterns (.env, id_rsa, *.pem, *.key, *.pfx, *.kdbx,|
|                                    | *.sqlite3, *.db, *.log) and 12 directory trees (.git, .venv). |
+------------------------------------+---------------------------------------------------------------+
| 2. AST Prompt Injection Sanitizer  | Scans document text and spoken transcripts via 11 regex AST   |
|    (Indirect Attack Prevention)    | patterns, replacing injection keywords with [SECURITY_REDACTED]|
+------------------------------------+---------------------------------------------------------------+
| 3. Code Fence Balancer             | Analyzes markdown syntax; asserts count('```') % 2 == 0;      |
|    (Syntax Parity Defense)         | automatically appends balancing fences to prevent breakout.   |
+------------------------------------+---------------------------------------------------------------+
| 4. Zero-Hallucination Threshold    | Asserts Okapi BM25 relevance score >= 0.15; on out-of-domain  |
|    (Anti-Hallucination Filter)     | queries, triggers refusal notice refusing unverified specs.   |
+------------------------------------+---------------------------------------------------------------+
```

### 6.1 Guardrail 1: Sensitive File Blocker (`is_sensitive_file`)
Prevents confidential enterprise credentials, private cryptographic keys, and local SQLite databases from being ingested into RAG memory:
- **14 Blocked File Patterns:** `.env`, `.env.*`, `id_rsa`, `id_ed25519`, `*.pem`, `*.key`, `*.cert`, `*.pfx`, `*.p12`, `*.kdbx`, `*.sqlite`, `*.sqlite3`, `*.db`, `*.log`.
- **12 Blocked Directory Trees:** `.git`, `.github`, `.idea`, `.vscode`, `node_modules`, `__pycache__`, `.pytest_cache`, `.mypy_cache`, `venv`, `.venv`, `env`, `dist`, `build`.

### 6.2 Guardrail 2: AST Indirect Prompt Injection Sanitizer (`sanitize_document_content`)
Protects against indirect prompt injection embedded within external markdown files or cloned repositories:
- Strips `<script>`, `<iframe>`, and HTML comment tags (`<!-- ... -->`).
- Replaces role-spoofing directives (`System:`, `Human:`, `ADMIN_OVERRIDE`, `Ignore previous instructions`) with `[SECURITY_REDACTED]`.

### 6.3 Guardrail 3: Code Fence Balancer
Ensures that malformed code fences do not disrupt downstream autonomous coding agent parsers:
- Detects odd counts of triple backticks (` ``` `).
- Automatically appends a trailing newline and closing ````\n``` ` prior to saving to disk or emitting to the client.

### 6.4 Guardrail 4: Zero-Hallucination BM25 Relevance Threshold
Prevents the RAG assistant from fabricating plausible-sounding technical answers on out-of-domain queries:
- If `max(bm25_score) < 0.15`, the engine refuses to answer with generic LLM training data, emitting:  
  `"Guardrail Notice: No sufficiently grounded context found in indexed documents matching query '{query}'. Refusing to hallucinate unverified specifications."`

---

## 7. Master Prompt Compiler & Zero-Shot Intermediate Representation

### 7.1 The Intermediate Representation (IR) Architecture
Autonomous coding tools require unambiguous execution plans. The `MasterPromptCompiler` (`src/master_prompt_compiler.py`) ingests the six generated artifacts and compiles them into a unified, zero-shot Intermediate Representation (`master_execution_bundle.md`):

```
+----------------------------------------------------------------------------------------------------+
|                           MASTER PROMPT COMPILER EXECUTION PIPELINE                                |
+----------------------------------------------------------------------------------------------------+
|  Inputs:                                                                                           |
|  • PRD.md (Business logic & Personas)                                                              |
|  • Architecture.md (C4 & PostgreSQL 16 DDL)                                                        |
|  • Flow.md (Sequences & State Machines)                                                            |
|  • design.md (Monolith Luxury Tokens)                                                              |
|  • tasks.md (Phased checklists & test commands)                                                    |
|                                                                                                    |
|  Compiler Validation Pipeline:                                                                     |
|  1. Syntax validation (Validates JSON / DDL / Mermaid syntax blocks)                                |
|  2. Fence parity check (Ensures balanced markdown code fences)                                     |
|  3. Environmental invariant header injection                                                       |
|  4. Topological file creation ordering                                                             |
|                                                                                                    |
|  Output:                                                                                           |
|  • master_execution_bundle.md (Zero-Shot Autonomous Execution Bundle)                              |
+----------------------------------------------------------------------------------------------------+
```

---

## 8. Autonomous GitHub PR Dispatcher & Version Control Engine

The `PRDispatcher` (`src/pr_dispatcher.py`) provides seamless version control integration:
- **Sanitized Feature Branching:** Automatically branches from `main` using the timestamped format `feature/voice-spec-YYYYMMDD-HHMMSS`.
- **Atomic Disk Synchronization:** Safely writes all generated specifications into the user's project repository under `docs/`.
- **Cryptographic & Authorship Invariants:** Commits are executed with the system identity:  
  `Author: maihun-rsc <rananjaychauhan93@gmail.com>`.
- **Automated Pull Request Creation:** Executes `gh pr create` via `subprocess.run`, populating title, executive summary, and labels (`automated-spec`, `vogenflow-v2`).
- **Resilient Fallback Mode:** In environments without an authenticated GitHub CLI, the dispatcher returns structured local Git shell commands (`git push origin <branch>`), ensuring zero pipeline failures.

---

## 9. Concurrency, Threading & Circuit Breaker State Machine

### 9.1 Concurrency Model & Async Event Loops
VoGenFlow 2.0 maintains a strictly non-blocking concurrency model:
- **Audio Ingestion Thread:** Microphone audio is captured via native OS C-callbacks in a background thread, writing directly into a thread-safe ring buffer.
- **FastAPI Async Event Loop:** HTTP and WebSocket connections are handled asynchronously via Uvicorn ASGI workers, preventing I/O waits from degrading API response times.
- **Council ThreadPoolExecutor:** Multi-agent LLM requests run in a pooled thread executor (`max_workers=4`), allowing parallel fan-out across independent models without blocking the ASGI event loop.

### 9.2 The 3-State Circuit Breaker Finite State Machine (`src/model_router.py`)
To prevent cascading API failures, retry storms, and unexpected token consumption, external model dispatches are governed by an explicit `CircuitBreaker` state machine:

```mermaid
stateDiagram-v2
    [*] --> CLOSED : Gateway Startup

    CLOSED --> OPEN : 3 Consecutive Network Failures\nOR Immediate HTTP 401 Unauthorized
    OPEN --> HALF_OPEN : Recovery Timeout (30.0s Elapsed)
    HALF_OPEN --> CLOSED : Successful Probe Request
    HALF_OPEN --> OPEN : Probe Request Fails

    state CLOSED {
        description: "Normal Operation - All requests dispatched to primary Groq LPU."
    }
    state OPEN {
        description: "Tripped State - Requests fast-fail immediately or reroute to local LM Studio."
    }
    state HALF_OPEN {
        description: "Testing Recovery - Allows a single canary request to test upstream health."
    }
```

- **Immediate Trip on 401 Unauthorized:** If an invalid BYOK API key is supplied, the circuit breaker trips to `OPEN` immediately (BUG-005 fix), aborting retries and preventing client hang.
- **Rate Pacing Lock:** Enforces a minimum interval between consecutive requests (`min_request_interval`), eliminating burst-induced HTTP 429 rate limit exceptions.

---

## 10. Interface Contracts & Pydantic API Schemas

Every data model and API payload across VoGenFlow 2.0 is validated using **Pydantic v2** contracts.

### 10.1 Core API Schemas (`src/api/server.py`)

```python
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class DeliberateRequest(BaseModel):
    transcript: str = Field(..., min_length=5, description="Spoken transcript or engineering prompt")
    preset: str = Field(default="standard", description="Council preset: standard, security_pentest, lean_sprint")
    byok_key: Optional[str] = Field(default=None, description="User's personal Groq API key")
    session_id: Optional[str] = Field(default=None, description="Client session identifier")
    target_dir: Optional[str] = Field(default=None, description="Optional target directory for direct file export")

class DeliberateResponse(BaseModel):
    session_id: str
    preset: str
    artifacts: Dict[str, str]
    telemetry: Dict[str, Any]
    status: str = "completed"

class RAGQueryRequest(BaseModel):
    query: str = Field(..., min_length=2, description="Search query or technical question")
    top_k: int = Field(default=3, ge=1, le=10, description="Maximum chunks to return")
    byok_key: Optional[str] = Field(default=None, description="User's Groq API key for synthesis")

class RAGQueryResponse(BaseModel):
    answer: str
    is_grounded: bool
    citations: List[Dict[str, Any]]
    latency_ms: float

class HealthResponse(BaseModel):
    status: str = "healthy"
    version: str = "2.0.0"
    stt_ready: bool
    rag_ready: bool
    indexed_chunks: int
```

---
*End of System Architecture Specification. Authored to Anti-Vibe Engineering Standard.*
