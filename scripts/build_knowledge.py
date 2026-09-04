"""Curated knowledge builder script."""
import json
import os

TEMPLATES = [
    {
        "id": "fastapi_async_service",
        "category": "backend",
        "keywords": ["fastapi", "rest", "api", "backend", "async", "service", "lifespan", "router", "endpoint"],
        "title": "Production FastAPI Async Microservice with Lifespan",
        "description": "Battle-tested async FastAPI application structure with lifespan management, structured JSON error handling, CORS, and dependency injection.",
        "snippet": (
            "from contextlib import asynccontextmanager\n"
            "from fastapi import FastAPI, Depends, HTTPException, status\n"
            "from fastapi.middleware.cors import CORSMiddleware\n"
            "from pydantic import BaseModel, Field\n"
            "import logging\n\n"
            "logger = logging.getLogger('service')\n\n"
            "@asynccontextmanager\n"
            "async def lifespan(app: FastAPI):\n"
            "    logger.info('Starting service connections and background caches...')\n"
            "    yield\n"
            "    logger.info('Tearing down connection pools cleanly...')\n\n"
            "app = FastAPI(title='Production Service', version='2.0.0', lifespan=lifespan)\n"
            "app.add_middleware(CORSMiddleware, allow_origins=['*'], allow_credentials=True, allow_methods=['*'], allow_headers=['*'])\n\n"
            "@app.get('/health', status_code=status.HTTP_200_OK)\n"
            "async def health_check():\n"
            "    return {'status': 'healthy', 'version': '2.0.0'}\n"
        )
    },
    {
        "id": "postgresql_ddl_relational",
        "category": "database",
        "keywords": ["postgres", "postgresql", "sql", "ddl", "schema", "table", "foreign key", "relational", "database", "rls"],
        "title": "PostgreSQL Multi-Tenant Relational Schema with RLS & Indices",
        "description": "Production PostgreSQL DDL with UUID keys, foreign key constraints, created_at/updated_at timestamps, composite indices on tenant_id, and Row-Level Security.",
        "snippet": (
            "CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";\n\n"
            "CREATE TABLE IF NOT EXISTS tenants (\n"
            "    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),\n"
            "    name VARCHAR(255) NOT NULL,\n"
            "    slug VARCHAR(100) UNIQUE NOT NULL,\n"
            "    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL\n"
            ");\n\n"
            "CREATE TABLE IF NOT EXISTS sessions (\n"
            "    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),\n"
            "    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,\n"
            "    title VARCHAR(255) NOT NULL,\n"
            "    audio_duration_seconds REAL DEFAULT 0.0,\n"
            "    transcript TEXT,\n"
            "    status VARCHAR(50) DEFAULT 'draft' CHECK (status IN ('draft', 'processing', 'completed', 'archived')),\n"
            "    metadata JSONB DEFAULT '{}'::jsonb,\n"
            "    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,\n"
            "    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL\n"
            ");\n\n"
            "CREATE INDEX IF NOT EXISTS idx_sessions_tenant ON sessions(tenant_id, created_at DESC);\n"
            "ALTER TABLE sessions ENABLE ROW LEVEL SECURITY;\n"
        )
    },
    {
        "id": "shadcn_tailwind_dashboard",
        "category": "frontend",
        "keywords": ["react", "frontend", "shadcn", "tailwind", "ui", "component", "dashboard", "lucide", "radix"],
        "title": "Shadcn / Tailwind Responsive Studio Card with Ambient Glow",
        "description": "React 19 + Tailwind v4 accessible component with hairline border, obsidian dark styling, and stateful interaction.",
        "snippet": (
            "import React, { useState } from 'react';\n"
            "import { Activity, Mic, ShieldCheck } from 'lucide-react';\n\n"
            "export const MonolithCard = ({ title, status, metric, children }) => {\n"
            "  const [active, setActive] = useState(false);\n"
            "  return (\n"
            "    <div className='p-6 rounded-xl bg-zinc-950/80 border border-zinc-800/80 hover:border-zinc-700 transition-all backdrop-blur-xl shadow-2xl'>\n"
            "      <div className='flex items-center justify-between mb-4'>\n"
            "        <h3 className='text-xs font-semibold tracking-widest text-zinc-400 uppercase font-mono'>{title}</h3>\n"
            "        <span className='inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-mono font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'>\n"
            "          <span className='w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse'></span>\n"
            "          {status}\n"
            "        </span>\n"
            "      </div>\n"
            "      <div className='text-2xl font-light text-zinc-100 font-sans tracking-tight mb-2'>{metric}</div>\n"
            "      <div className='text-sm text-zinc-400'>{children}</div>\n"
            "    </div>\n"
            "  );\n"
            "};\n"
        )
    },
    {
        "id": "celery_redis_worker",
        "category": "worker",
        "keywords": ["celery", "redis", "background", "queue", "worker", "async", "job", "task"],
        "title": "Celery with Redis Broker Background Queue Architecture",
        "description": "High-throughput asynchronous background job dispatcher with retry backoff and progress tracking.",
        "snippet": (
            "from celery import Celery\n"
            "import os\n\n"
            "REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')\n"
            "celery_app = Celery('vogenflow_worker', broker=REDIS_URL, backend=REDIS_URL)\n"
            "celery_app.conf.update(\n"
            "    task_serializer='json',\n"
            "    accept_content=['json'],\n"
            "    result_serializer='json',\n"
            "    timezone='UTC',\n"
            "    enable_utc=True,\n"
            "    task_acks_late=True,\n"
            "    worker_prefetch_multiplier=1\n"
            ")\n\n"
            "@celery_app.task(bind=True, max_retries=3, default_retry_delay=5)\n"
            "def process_audio_synthesis(self, session_id: str, audio_path: str):\n"
            "    try:\n"
            "        return {'status': 'completed', 'session_id': session_id}\n"
            "    except Exception as exc:\n"
            "        raise self.retry(exc=exc)\n"
        )
    },
    {
        "id": "c4_mermaid_architecture",
        "category": "architecture",
        "keywords": ["mermaid", "c4", "architecture", "diagram", "flowchart", "sequence", "graph"],
        "title": "Safe C4 Container Architecture Diagram (Mermaid)",
        "description": "Clean, syntactically safe C4 container flow with escaped labels and distinct styling classes.",
        "snippet": (
            "flowchart TD\n"
            "    classDef client fill:#0d1117,stroke:#30363d,stroke-width:1px,color:#c9d1d9;\n"
            "    classDef gateway fill:#161b22,stroke:#388bfd,stroke-width:1px,color:#58a6ff;\n"
            "    classDef service fill:#21262d,stroke:#238636,stroke-width:1px,color:#3fb950;\n\n"
            "    Client[\"Desktop / Web Client<br/>(Tauri v2 + React 19)\"]:::client\n"
            "    Gateway[\"FastAPI API Gateway and WebSocket<br/>(Port 8000)\"]:::gateway\n"
            "    Router[\"Task-Specific Multi-Model Router<br/>(Groq LPU)\"]:::service\n"
            "    Store[\"Local Store / BM25 Knowledge Catalog\"]:::service\n\n"
            "    Client <-->|WebSocket Stream / JSON| Gateway\n"
            "    Gateway -->|Spoken Query| Router\n"
            "    Gateway -->|Context Retrieval| Store\n"
        )
    },
    {
        "id": "master_bundle_ir",
        "category": "compiler",
        "keywords": ["bundle", "ir", "intermediate representation", "claude code", "antigravity", "prompt", "code generation"],
        "title": "Zero-Shot Intermediate Representation (IR) Master Execution Bundle",
        "description": "The standardized Markdown format that autonomous coding agents consume to write complete codebase implementations without human interaction.",
        "snippet": (
            "# MASTER EXECUTION BUNDLE: [FEATURE_NAME]\n\n"
            "## 1. Architectural Scope & Target Files\n"
            "- `[NEW] path/to/file.py`: Core implementation logic\n"
            "- `[NEW] tests/test_file.py`: Unit test verification\n\n"
            "## 2. Low-Level Implementation Contracts\n\n"
            "### File: `path/to/file.py`\n"
            "```python\n"
            "# Complete, compilable source code\n"
            "```\n\n"
            "## 3. Automated Verification Checklist\n"
            "- [ ] Run test suite: `python -m unittest tests/test_file.py`\n"
            "- [ ] Verify zero syntax errors and 100% test pass rate\n"
        )
    }
]

def main():
    os.makedirs(r"E:\voice-insight-generation\data", exist_ok=True)
    out_path = r"E:\voice-insight-generation\data\curated_knowledge.json"
    payload = {
        "version": "2.0.0",
        "updated_at": "2026-09-04T10:00:00Z",
        "templates": TEMPLATES
    }
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    print(f"Generated {out_path} with {len(TEMPLATES)} templates successfully.")

if __name__ == "__main__":
    main()
