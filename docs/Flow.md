# ⚙️ VoGenFlow 2.0: System Execution Flow & Lifecycle (Flow.md)
> **Document Type:** Production Execution Flow, Sequence Topologies & Lifecycle Manual  
> **Status:** Active & Validated (Anti-Vibe Engineering Standard)  
> **Version:** 2.0.0 Production  
> **Target Audiences:** Lead Architects, Systems Engineers, DevOps Integrators & Autonomous Agents  

---

## 📑 Table of Contents
1. [Unified System Entry Points & Server Lifespans](#1-unified-system-entry-points--server-lifespans)
2. [Real-Time Audio Streaming & Sub-Second Transcription Sequence](#2-real-time-audio-streaming--sub-second-transcription-sequence)
3. [The 3-Stage Scatter-Gather Council Deliberation Sequence](#3-the-3-stage-scatter-gather-council-deliberation-sequence)
4. [Dual-Mode RAG Retrieval & Document Query Resolution Flow](#4-dual-mode-rag-retrieval--document-query-resolution-flow)
5. [Autonomous GitHub PR Dispatch Sequence](#5-autonomous-github-pr-dispatch-sequence)
6. [Comprehensive Function Call Hierarchy & Invocation Matrix](#6-comprehensive-function-call-hierarchy--invocation-matrix)
7. [Error Recovery, Failover Dynamics & Circuit Breaker Transitions](#7-error-recovery-failover-dynamics--circuit-breaker-transitions)
8. [Data Transformation & Multi-Format Artifact Pipeline](#8-data-transformation--multi-format-artifact-pipeline)

---

## 1. Unified System Entry Points & Server Lifespans

VoGenFlow 2.0 operates through three distinct, non-conflicting operational entry points:

```
                                [SYSTEM ENTRY POINTS]
                                          │
         ┌────────────────────────────────┼────────────────────────────────┐
         ▼                                ▼                                ▼
[1. Cloud Web SaaS]             [2. Terminal CLI]              [3. Native Desktop Shell]
uvicorn src.api.server:app      python -m src.cli ...          Tauri v2 (Rust 1.75+)
Port 8000 / Web Studio          Headless Automation            Cross-Platform Desktop
```

### 1.1 Entry Point A: Cloud Web SaaS (`uvicorn src.api.server:app`)
- **Execution Command:** `python -m uvicorn src.api.server:app --host 0.0.0.0 --port 8000 --reload`
- **Lifespan Context Manager (`src/api/server.py:lifespan`):**
  1. **Singleton Initialization:** Instantiates in-memory singletons: `CuratedKnowledgeDB`, `STTService`, and `LocalRAGEngine`.
  2. **Knowledge Pre-Seeding:** Ingests 16 pre-seeded enterprise blueprints from `data/curated_knowledge.json`.
  3. **Local Codebase Pre-Indexing:** Scans the active repository root (excluding `.git`, `node_modules`, and secret files), tokenizing code chunks into the in-memory Okapi BM25 inverted index.
  4. **Static Route Mounting:** Mounts `web_app/` as the static root at `/`, serving the Monolith Luxury Command Studio (`web_app/index.html`).
  5. **Graceful Teardown:** Upon `SIGINT`/`SIGTERM`, cleanly flushes in-memory session caches, unlinks temporary audio files, and terminates active thread pools.

### 1.2 Entry Point B: Terminal Automation CLI (`src/cli.py`)
- **Execution Command:** `python -m src.cli [options]`
- **Supported Operational Modes:**
  - **Live Microphone Recording:** `python -m src.cli record --duration 15 --output temp_audio/my_spec.wav`
  - **Acoustic Transcription:** `python -m src.cli transcribe temp_audio/my_spec.wav --provider groq`
  - **Direct Council Deliberation:** `python -m src.cli deliberate --transcript "Build a Redis-backed rate limiter" --preset standard --target-dir ./out`
  - **Knowledge Query:** `python -m src.cli query --text "How is tenant isolation implemented in DDL?"`

### 1.3 Entry Point C: Native Desktop Shell (Tauri v2 in Rust)
- **Execution Command:** `cargo tauri dev` or `VoGenFlow.exe`
- **Architecture:** The Rust runtime boots a background local FastAPI sidecar process, captures microphone audio directly through the OS audio subsystem (PortAudio/CoreAudio), and projects the Command Studio interface within a high-performance native OS webview (WebView2 on Windows, WebKitGTK on Linux, WKWebView on macOS).

---

## 2. Real-Time Audio Streaming & Sub-Second Transcription Sequence

The live audio ingestion sequence captures raw microphone buffers, calculates real-time RMS acoustic power, and streams telemetry back to the client interface over WebSockets:

```mermaid
sequenceDiagram
    autonumber
    actor Developer as Developer / Creator
    participant WebUI as Web Command Studio (Web Audio API)
    participant WS as WebSocket Gateway (/ws/stream)
    participant STT as STTService (Groq Whisper Client)
    participant GroqAPI as Groq Whisper LPU (Cloud)

    Developer->>WebUI: Clicks "🎙️ Record" (Ambient Voice Pill)
    WebUI->>WS: WebSocket Connect (ws://localhost:8000/ws/stream)
    WS-->>WebUI: Connection Accepted (101 Switching Protocols)
    WebUI->>WS: JSON Control Frame {"action": "start_recording"}
    WS->>WS: Initialize in-memory PCM bytearray buffer

    loop Every 50ms Audio Interval (16kHz Mono 16-bit PCM)
        Developer->>WebUI: Speaks engineering thoughts aloud
        WebUI->>WS: Binary Frame (Raw PCM bytes: ArrayBuffer)
        WS->>WS: compute_rms(chunk) -> Compute Normalized RMS & dB
        WS-->>WebUI: JSON Telemetry {"type": "audio_telemetry", "rms": 0.42, "db": -7.5}
        WebUI->>WebUI: Render real-time Gaussian soundwave bars
    end

    Developer->>WebUI: Clicks "🛑 Stop Recording"
    WebUI->>WS: JSON Control Frame {"action": "stop_recording"}
    WS->>WS: Flush PCM buffer to temporary WAV container (temp_audio/temp_recording_*.wav)
    WS->>STT: transcribe_audio(wav_path)
    STT->>GroqAPI: POST /v1/audio/transcriptions (multipart/form-data)
    GroqAPI-->>STT: 200 OK {text: "Build a multi-tenant B2B churn analytics engine...", duration: 14.2}
    STT-->>WS: Return STTResult (transcript, segments, latency: 318ms)
    WS-->>WebUI: JSON {"type": "transcript_ready", "transcript": "...", "latency_ms": 318}
    WS->>WS: Clean up temporary WAV file
    WebUI->>WebUI: Populate Specification Studio & activate Council trigger
```

---

## 3. The 3-Stage Scatter-Gather Council Deliberation Sequence

The core multi-agent reasoning pipeline executes an asynchronous Scatter-Gather Directed Acyclic Graph (DAG) across three deterministic stages:

```mermaid
sequenceDiagram
    autonumber
    actor Developer
    participant WebUI as Web Command Studio
    participant API as FastAPI Gateway (/api/council/deliberate)
    participant Router as ModelRouter & CircuitBreaker
    participant PM as Lead Strategist (pm_agent)
    participant FanOut as ThreadPoolExecutor (max_workers=4)
    participant Arch as System Architect (architect_agent)
    participant UI as UI/UX Engineer (ui_agent)
    participant Sys as Systems Engineer (systems_agent)
    participant Agile as Agile Lead (agile_agent)
    participant Diff as Delta Refiner (diff_agent)
    participant Disk as Local Project Repository (docs/)

    Developer->>WebUI: Clicks "🏛️ Deliberate Council"
    WebUI->>API: POST /api/council/deliberate {transcript, preset: "standard", byok_key}
    API->>API: Validate Trial Quota (TrialQuotaManager)

    rect rgb(20, 20, 20)
        note over PM,Router: STAGE 1: CANONICAL PRD SYNTHESIS
        API->>PM: deliberate(transcript, rag_context)
        PM->>Router: dispatch(prompt, role="pm")
        Router-->>PM: Emits Canonical PRD.md
        PM->>API: Register PRD.md as Single Source of Truth on Blackboard (CAB)
    end

    rect rgb(25, 25, 30)
        note over FanOut,Agile: STAGE 2: PARALLEL SCATTER FAN-OUT (Concurrent Execution)
        API->>FanOut: dispatch_parallel(PRD_context, rag_context)
        par Concurrent Agent Invocations
            FanOut->>Arch: deliberate() -> C4 Architecture + PostgreSQL 16 DDL
            FanOut->>UI: deliberate() -> Monolith Luxury Tokens + Viewports
            FanOut->>Sys: deliberate() -> Sequence Flows + State Machines
            FanOut->>Agile: deliberate() -> Phased Task Checklists + Test Commands
        end
        Arch-->>FanOut: Emits Architecture.md
        UI-->>FanOut: Emits design.md
        Sys-->>FanOut: Emits Flow.md
        Agile-->>FanOut: Emits tasks.md
        FanOut->>API: Gather all 4 artifacts onto Blackboard (CAB)
    end

    rect rgb(30, 20, 20)
        note over Diff,Router: STAGE 3: SYNTAX VALIDATION & BUNDLE COMPILATION
        API->>Diff: deliberate(all_artifacts)
        Diff->>Diff: Validate code fence parity (count('```') % 2 == 0)
        Diff->>Diff: Compile master_execution_bundle.md
        Diff-->>API: Emits validated artifact suite
    end

    opt Direct Disk Export
        API->>Disk: Write PRD.md, Architecture.md, Flow.md, design.md, tasks.md
    end

    API-->>WebUI: 200 OK {status: "completed", artifacts: {...}, telemetry: {...}}
    WebUI->>WebUI: Mount artifacts in Studio Tabs & Render Zoomable Mermaid Diagram
```

---

## 4. Dual-Mode RAG Retrieval & Document Query Resolution Flow

When a developer queries the embedded RAG assistant, the engine routes between **Grounded Q&A Mode** and **Architectural Advisory Fallback Mode**:

```mermaid
sequenceDiagram
    autonumber
    actor Developer
    participant WebUI as RAG Chat Drawer
    participant API as FastAPI (/api/rag/query)
    participant RAG as LocalRAGEngine (Okapi BM25)
    participant Guard as Security Guardrails & Sanitizer
    participant Router as ModelRouter (Groq LPU)

    Developer->>WebUI: Submits query: "How is rate limiting enforced in the API gateway?"
    WebUI->>API: POST /api/rag/query {query, top_k: 3, byok_key}
    API->>Guard: sanitize_document_content(query)
    Guard-->>API: Clean query (Stripped of injection tokens)
    API->>RAG: query_knowledge_base(clean_query, top_k=3)
    RAG->>RAG: Tokenize & compute BM25 scores across indexed chunks

    alt BM25 Max Score >= 0.15 (Grounded Context Found)
        RAG-->>API: Returns Ranked DocumentChunk array with citations
        API->>Router: Synthesize answer with grounded context prompt
        Router-->>API: Emits precise answer citing exact [Filename §ChunkID]
        API-->>WebUI: 200 OK {answer: "...", is_grounded: true, citations: [...]}
    else BM25 Max Score < 0.15 (Out-of-Domain or Conceptual Query)
        RAG-->>API: Returns empty context array (Refusal Tripwire)
        API->>API: Evaluate query type: Architectural Strategy vs. Factual Code
        alt Architectural Advisory Query
            API->>Router: Dispatch Advisory Synthesis prompt (General Best Practices)
            Router-->>API: Emits strategic guidance prefixed with [ARCHITECTURAL ADVISORY // SYNTHESIS]
            API-->>WebUI: 200 OK {answer: "[ARCHITECTURAL ADVISORY // SYNTHESIS] ...", is_grounded: false}
        else Ungrounded Hallucination Trap
            API-->>WebUI: 200 OK {answer: "Guardrail Notice: No sufficiently grounded context found matching query. Refusing to hallucinate unverified specifications.", is_grounded: false}
        end
    end
```

---

## 5. Autonomous GitHub PR Dispatch Sequence

The automated version control workflow provisions a dedicated Git branch, stages all generated files, executes an atomic commit under verified system authorship, and opens a GitHub Pull Request:

```mermaid
sequenceDiagram
    autonumber
    actor Developer
    participant WebUI as Web Command Studio
    participant API as FastAPI (/api/pr/dispatch)
    participant Dispatcher as PRDispatcher (src/pr_dispatcher.py)
    participant GitCLI as Native Git CLI (subprocess)
    participant GitHubCLI as GitHub CLI (gh pr create)
    participant GitHub as Remote GitHub Repository

    Developer->>WebUI: Clicks "🚀 Open GitHub Pull Request"
    WebUI->>API: POST /api/pr/dispatch {title, session_id, target_dir}
    API->>Dispatcher: dispatch_pr(title, session_id, target_dir)

    Dispatcher->>GitCLI: git status --porcelain (Verify repository root)
    GitCLI-->>Dispatcher: Clean status verified

    Dispatcher->>GitCLI: git checkout -b feature/voice-spec-20261108-073000
    GitCLI-->>Dispatcher: Switched to new feature branch

    Dispatcher->>Dispatcher: Write PRD.md, Architecture.md, Flow.md, design.md, tasks.md to docs/
    Dispatcher->>GitCLI: git add docs/
    GitCLI-->>Dispatcher: Files staged

    Dispatcher->>GitCLI: git commit -m "[VoGenFlow] Autonomous Specification Suite" --author "maihun-rsc <rananjaychauhan93@gmail.com>"
    GitCLI-->>Dispatcher: [feature/voice-spec-20261108-073000 abc1234] 5 files changed, 1420 insertions

    Dispatcher->>GitHubCLI: gh pr create --title "[VoGenFlow] New Architecture Specification" --body "..."
    alt GitHub CLI Available & Authenticated
        GitHubCLI->>GitHub: Open Pull Request via GitHub REST API
        GitHub-->>GitHubCLI: 201 Created (https://github.com/org/repo/pull/42)
        GitHubCLI-->>Dispatcher: Return PR URL
        Dispatcher-->>API: {"status": "success", "pr_url": "https://github.com/org/repo/pull/42"}
    else GitHub CLI Missing or Unauthenticated
        Dispatcher-->>API: {"status": "fallback", "git_instructions": "git push origin feature/voice-spec-20261108-073000"}
    end

    API-->>WebUI: 200 OK with Live PR Link or Copyable Terminal Commands
```

---

## 6. Comprehensive Function Call Hierarchy & Invocation Matrix

The following matrix maps every user interaction directly to its executing classes, methods, and destination states:

| User Interaction | Trigger Method / Route | Underlying Call Hierarchy | Target Class & Function | Output Artifact / Destination State |
| :--- | :--- | :--- | :--- | :--- |
| **Click "Record"** | UI Event Listener | `WebSocket.send({"action": "start_recording"})` | `src/api/server.py:websocket_stream` | In-memory PCM bytearray buffer initialized |
| **Stream Audio PCM** | `ScriptProcessorNode` | `WebSocket.send(binaryBuffer)` | `src/api/server.py:compute_rms` | Emits `audio_telemetry` JSON frame |
| **Click "Stop Recording"**| UI Event Listener | `WebSocket.send({"action": "stop_recording"})` | `src/stt_service.py:transcribe_audio` | Emits `transcript_ready` JSON frame |
| **Audio File Upload** | `POST /api/stt/transcribe` | Multipart upload handler | `src/stt_service.py:transcribe_file` | Returns `STTResult` with timestamps |
| **Index Project Code** | `POST /api/rag/index` | Lifespan or manual trigger | `src/rag_engine.py:LocalRAGEngine.index_directory` | In-memory Okapi BM25 inverted index |
| **Run Council DAG** | `POST /api/council/deliberate` | REST endpoint handler | `src/council_engine.py:CouncilEngine.deliberate` | Emits 6 specification markdown documents |
| **RAG Grounded Query** | `POST /api/rag/query` | REST endpoint handler | `src/rag_engine.py:LocalRAGEngine.query_knowledge_base`| Returns structured Q&A answer with citations |
| **Compile IR Bundle** | Council Stage 3 | `CouncilEngine._compile_bundle` | `src/master_prompt_compiler.py:MasterPromptCompiler.compile` | `output/master_execution_bundle.md` |
| **Export GitHub PR** | `POST /api/pr/dispatch` | REST endpoint handler | `src/pr_dispatcher.py:PRDispatcher.dispatch_pr` | Remote GitHub Pull Request via `gh` CLI |
| **Export Master PDF** | User Shell / Script | Standalone compiler script | `docs/generate_pdf_documentation.py:generate_master_pdf` | `docs/Voice_Insights_Master_Documentation.pdf` |

---

## 7. Error Recovery, Failover Dynamics & Circuit Breaker Transitions

VoGenFlow 2.0 incorporates deterministic error handling to ensure zero unhandled server crashes:

### 7.1 WebSocket Abrupt Disconnection Guard (BUG-003 Resolution)
When a client closes their browser tab or loses Wi-Fi during an active audio streaming session:
- The WebSocket server catches `(WebSocketDisconnect, RuntimeError)` cleanly.
- The server releases the client lock, purges the in-memory PCM audio buffer, and logs a clean connection closure without throwing unhandled tracebacks.

### 7.2 Fatal Authentication & Instant Circuit Breaker Trip (BUG-005 Resolution)
When a user provides an invalid or expired Groq API key:
- The upstream API responds with HTTP 401 Unauthorized.
- `CircuitBreaker` instantly transitions from `CLOSED` to `OPEN` state, bypassing retry loops and preventing 6-second client UI hangs.
- An immediate structured error is emitted: `{"error": "Invalid Groq API Key. Please verify your BYOK credentials."}`.

### 7.3 Burst Rate Pacing & HTTP 429 Mitigation
To eliminate rate-limiting exceptions during parallel council fan-outs:
- `ModelRouter` enforces a `min_request_interval` (0.25s) between outbound HTTP dispatches.
- If HTTP 429 is encountered, the router catches the exception, engages exponential backoff with jitter ($T_{\text{wait}} = 2^n + \text{rand}(0, 1)$), or fails over to deterministic offline blueprints.

### 7.4 Air-Gapped Local LM Studio Offline Failover
If the workstation loses internet connectivity:
- `ModelRouter` pings the local LM Studio endpoint (`http://localhost:1234/v1`) via a non-blocking 30ms socket probe.
- If LM Studio Bionic is active, traffic routes locally with zero telemetry escaping the workstation.
- If no local model is detected, the engine activates deterministic offline blueprint generation.

---

## 8. Data Transformation & Multi-Format Artifact Pipeline

The transformation lifecycle converts raw physical sound pressure into verified, deployable software assets:

```
[1. Acoustic Sound Waves (Vocal Cord Vibration)]
   │
   ▼
[2. Raw PCM Digital Audio (16kHz, 16-bit Mono Integers)]
   │
   ▼
[3. Transcribed Lexical Text (Whisper LPU Sub-Second Tokens)]
   │
   ▼
[4. Decomposed Sub-Queries & Inverted Index Token Scoring (BM25 Grounding)]
   │
   ▼
[5. Multi-Agent Structured Markdown Documents (PRD, Architecture, DDL, Flow, Design, Tasks)]
   │
   ▼
[6. Machine-Executable Intermediate Representation (master_execution_bundle.md)]
   │
   ▼
[7. Version-Controlled Production Assets (Git Branch, GitHub PR & Styled Master PDF)]
```

---
*End of System Execution Flow & Lifecycle Specification. Authored to Anti-Vibe Engineering Standard.*
