# Vo-Gen-Flow: Voice-based Generative AI for Workflows
> **Autonomous Cognitive Architecture Platform & Multi-Model Multi-Agent Council**  
> **Proprietary Commercial IP** | Author: `maihun-rsc <rananjaychauhan93@gmail.com>`

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-3776AB.svg?logo=python&logoColor=white)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.129.2-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![WebSockets](https://img.shields.io/badge/WebSocket-Real--Time%20Streaming-black.svg?logo=websocket&logoColor=white)](src/api/server.py)
[![Tauri v2](https://img.shields.io/badge/Tauri-v2%20Rust%20Native-24C8D8.svg?logo=tauri&logoColor=white)](src-tauri/)
[![STT-Groq Whisper](https://img.shields.io/badge/STT-Groq%20Whisper%20LPU-F55036.svg)](https://groq.com/)
[![Council-MoE](https://img.shields.io/badge/Council-120B%20%2B%20Qwen3.6%20%2B%2020B-0467DF.svg)](docs/Council_Master_Prompt.md)
[![Tests-Passing](https://img.shields.io/badge/Tests-35%2F35%20Passing%20(100%25)-success.svg)](tests/)
[![Security-DAST Pentest Verified](https://img.shields.io/badge/Security-DAST%20Audit%20Verified-emerald.svg)](tests/test_security_pentest.py)

---

## 1. Executive Summary

**Vo-Gen-Flow** is an industrial-grade, commercial voice-to-workflow generative AI platform designed for tech leads, systems architects, and technical founders. It transforms spontaneous spoken technical brainstorming and multi-speaker architecture debates into publication-ready engineering specifications (`PRD.md`, C4 Mermaid `Architecture.md`, `Flow.md`, `tasks.md`, `design_proposal.md`) and compiles a zero-shot Intermediate Representation (`master_execution_bundle.md`) for autonomous coding agents (Claude Code, Antigravity, Codex) with automated Git Pull Requests.

### Key Architectural Differentiators
1. **Bring-Your-Own-Key (BYOK) Architecture:** Users supply their own Groq API keys or connect to air-gapped local Ollama models. The SaaS operator carries **\$0.00 model inference liability**, yielding an unprecedented **99.98% Gross Profit Margin** (\$11.88M ARR at 10,000 MAU against only \$135/mo in server consumables).
2. **Sub-Second Groq Whisper LPU STT:** Transcribes 60 seconds of complex audio in ~300ms with zero client GPU dependency.
3. **Curated Engineering Knowledge Catalog (`data/curated_knowledge.json`):** In-memory Okapi BM25 pattern retriever injecting battle-tested production templates (FastAPI lifespan, PostgreSQL DDL with RLS, Shadcn UI blocks, Redis background workers) directly into prompts.
4. **Task-Specific Multi-Model Routing:** Distributes council roles across specialized models (`openai/gpt-oss-120b` for strategy/PRD, `qwen/qwen3.6-27b` for C4 diagrams and PostgreSQL DDL, `openai/gpt-oss-20b` for triage and IR bundling) with strict 2-second rate-limit pacing.
5. **Dual-Target Surface (Web SaaS + Tauri v2 Desktop):** A luxury reductionist interface inspired by Range Rover and Rolls-Royce digital design (obsidian black `#010308`, midnight sapphire accents, hairline borders, no emojis) and a global desktop hotkey `Ctrl+Shift+V` / `Cmd+Shift+V`.
6. **Automated DAST Security & Pentesting:** Verified resilience against prompt injection, delimiter breakouts, path traversal, and BYOK credential leakage.

---

## 2. System Architecture & Component Topology

```mermaid
flowchart TD
    subgraph Client_Surfaces ["1. Client Surfaces (Dual-Target)"]
        WebClient["Web SaaS Client (React 19 + Tailwind + Lucide)"]
        DesktopClient["Desktop Shell (Tauri v2 Rust + Global Hotkey Ctrl+Shift+V)"]
    end

    subgraph API_Gateway ["2. FastAPI & Streaming WebSocket Gateway"]
        Gateway["FastAPI Server (:8000)"]
        WS["WebSocket Stream /ws/stream (16kHz PCM & Volume RMS)"]
        REST["REST API (/health, /api/council/deliberate, /api/stt/transcribe)"]
        WebClient <-->|WebSocket / REST| Gateway
        DesktopClient <-->|IPC / Localhost| Gateway
    end

    subgraph Intelligence_Core ["3. Intelligence Core & Dual Grounding"]
        STT["⚡ Groq Whisper LPU (sub-400ms STT)"]
        Catalog["📚 Curated Knowledge Catalog (In-Memory BM25)"]
        LocalRAG["🔍 Local Codebase AST RAG Engine"]
        Router["🧠 Multi-Model Router with 2s Rate-Limit Pacing & Circuit Breakers"]
        
        Gateway --> STT
        STT --> Router
        Catalog --> Router
        LocalRAG --> Router
    end

    subgraph Multi_Model_Council ["4. Autonomous Council Execution DAG"]
        Router --> M_PM["👑 Principal PM (openai/gpt-oss-120b) -> PRD.md"]
        M_PM --> M_Arch["🏛️ System Architect (qwen/qwen3.6-27b) -> Architecture.md"]
        M_PM --> M_UI["🎨 Staff UI/UX (qwen/qwen3.6-27b) -> design_proposal.md"]
        M_Arch & M_UI --> M_Sys["⚙️ Systems Engineer (openai/gpt-oss-120b) -> Flow.md"]
        M_Sys --> M_Agile["📋 Agile Delivery (qwen/qwen3.6-27b) -> tasks.md"]
        M_PM & M_Arch & M_UI & M_Sys & M_Agile --> M_Diff["🔍 Delta Refiner (openai/gpt-oss-20b)"]
    end

    subgraph Autonomous_Dispatch ["5. Execution & Dispatch Layer"]
        M_Diff --> Compiler["📦 Master Prompt Compiler -> master_execution_bundle.md"]
        Compiler --> PRDispatcher["🚀 Autonomous Git PR Dispatcher (Feature Branch & GitHub PR)"]
        Compiler --> PDFReport["📑 30+ Page Master PDF Documentation"]
    end
```

---

## 3. The 4 Engineering Build Phases (Complete & Verified)

| Phase | Core Deliverables | Verification Status |
| :--- | :--- | :--- |
| **Phase 1: Multi-Model AI Council** | `data/curated_knowledge.json`, `src/knowledge_db.py`, `src/model_router.py`, `src/council_engine.py` | Verified (5/5 Unit Tests Passing) |
| **Phase 2: FastAPI WebSocket Bridge** | `src/api/server.py`, `/ws/stream`, Web Audio API recording in `frontend_demo.html` | Verified (6/6 Integration Tests Passing) |
| **Phase 3: Autonomous PR Dispatcher** | `src/master_prompt_compiler.py`, `src/pr_dispatcher.py`, atomic git commits | Verified (4/4 Dispatcher Tests Passing) |
| **Phase 4: Desktop Packaging & Pentest** | `src-tauri/` (Tauri v2), `tests/test_security_pentest.py`, `docs/Feasibility_and_Unit_Economics.md`, Master PDF | Verified (6/6 Pentest & 35/35 Total Tests Passing) |

---

## 4. Automated Test Suite & Verification Results

```bash
# Execute the complete project test suite
python -m unittest discover tests
```

Output:
```
Ran 35 tests in 8.642s
OK (100% test pass rate)
```

### Verified Test Matrix:
- `tests/test_knowledge_db.py`: BM25 pattern indexing, keyword search, prompt formatting.
- `tests/test_router.py`: Role model mapping, circuit breaker trips, fallback generation, 2s rate-pacing.
- `tests/test_council.py`: Council presets (`standard`, `security_pentest`, `lean_sprint`), artifact persistence.
- `tests/test_api.py`: REST health, preset retrieval, deliberation, RMS audio computation, WebSocket ping/pong.
- `tests/test_dispatcher.py`: Master execution bundle compilation, syntax validation, git branch creation, rollback.
- `tests/test_security_pentest.py`: Prompt injection sanitization, path traversal blocking, BYOK key scrubbing, WebSocket flood stability.
- `tests/test_stt.py`, `tests/test_recorder.py`, `tests/test_rag.py`: Audio capture, transcription, and codebase chunking.

---

## 5. Quick Start & Execution Guide

### Prerequisites
- Python 3.10+
- (Optional) Rust + Cargo for Tauri v2 native desktop compilation
- (Optional) Groq API Key (`GROQ_API_KEY`) for live LPU acceleration

### 1. Installation
```bash
# Clone the private repository
git clone https://github.com/maihun-rsc/voice-insight-generation.git
cd voice-insight-generation

# Install Python dependencies
pip install -r requirements.txt
```

### 2. Configure Environment (BYOK)
Create a `.env` file in the project root:
```env
GROQ_API_KEY=gsk_your_groq_api_key_here
AUDIO_SAMPLE_RATE=16000
DEFAULT_GROQ_STT_MODEL=whisper-large-v3-turbo
```

### 3. Launch the API Gateway & Streaming Server
```bash
python src/api/server.py
```
The API server starts at `http://localhost:8000` with documentation available at `http://localhost:8000/docs`.

### 4. Launch the Monolith Luxury Studio
Open `frontend_demo.html` in any modern web browser or run:
```bash
# Or launch the native desktop shell (requires Tauri CLI):
cargo tauri dev
```

---

## 6. Commercial Feasibility & Financial Model Snapshot

Detailed analysis available in [docs/Feasibility_and_Unit_Economics.md](docs/Feasibility_and_Unit_Economics.md).

- **Starter Tier:** \$49 / user / month
- **Professional Tier:** \$149 / user / month
- **Enterprise Monolith:** \$499 / user / month
- **Blended ARPU:** \$99 / user / month
- **10,000 Active Users:** **\$990,000 MRR (\$11.88M ARR)**
- **Total Server Consumables:** **\$135.00 / month** (FastAPI ECS Fargate + Supabase PostgreSQL + Cloudflare CDN)
- **Net Gross Margin:** **99.98%**

---

## 7. Security Policy & Responsible Disclosure
Vo-Gen-Flow implements defensive prompt sandboxing, strict input sanitization, and automated secret scrubbing. For security audits or bug reports, contact `maihun-rsc <rananjaychauhan93@gmail.com>`.

**License:** Proprietary Commercial Intellectual Property. All rights reserved.
