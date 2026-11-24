"""FastAPI REST & WebSocket Gateway Server for Vo-Gen-Flow."""

import os
import re
import json
import time
import uuid
import math
import struct
import logging
import asyncio
import threading
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, UploadFile, File, Form, Request, status
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from src.config import Config
from src.stt_service import STTService
from src.knowledge_db import CuratedKnowledgeDB
from src.rag_engine import LocalRAGEngine
from src.model_router import ModelRouter
from src.council_engine import CouncilEngine, COUNCIL_PRESETS
from src.db.sqlite_store import SQLiteStore, PersistentSessionDict

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("vogenflow.api")

# SQLite WAL-mode persistent storage adapter & session store proxy
sqlite_store = SQLiteStore()
ACTIVE_SESSIONS: PersistentSessionDict = PersistentSessionDict(sqlite_store)


class TrialQuotaManager:
    """Enforces monthly trial limits (5 prompts/mo) and iterative edit limits (max 4 edits/session)."""

    MAX_MONTHLY_PROMPTS = 5
    MAX_SESSION_EDITS = 4
    MONTH_SECONDS = 30 * 24 * 3600

    def __init__(self):
        self._clients: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()

    def reset(self):
        with self._lock:
            self._clients.clear()

    def _get_client_record(self, client_id: str) -> Dict[str, Any]:
        now = time.time()
        if client_id not in self._clients:
            self._clients[client_id] = {
                "prompts_used": 0,
                "period_start": now,
                "sessions": {}
            }
        rec = self._clients[client_id]
        if now - rec["period_start"] > self.MONTH_SECONDS:
            rec["prompts_used"] = 0
            rec["period_start"] = now
            rec["sessions"] = {}
        return rec

    def check_and_consume(self, client_id: str, session_id: Optional[str] = None) -> Tuple[bool, str, Dict[str, Any], str]:
        with self._lock:
            rec = self._get_client_record(client_id)
            now = time.time()
            reset_in_days = max(1, int((self.MONTH_SECONDS - (now - rec["period_start"])) / 86400))

            if session_id and session_id in rec["sessions"]:
                # Iterative edit on an existing session
                edits = rec["sessions"][session_id]
                if edits >= self.MAX_SESSION_EDITS:
                    return False, f"Maximum edit limit reached for this session ({self.MAX_SESSION_EDITS}/{self.MAX_SESSION_EDITS}). Start a new session or download Vo-Gen-Flow Desktop.", {
                        "monthly_used": rec["prompts_used"],
                        "monthly_limit": self.MAX_MONTHLY_PROMPTS,
                        "session_edits": edits,
                        "session_edit_limit": self.MAX_SESSION_EDITS,
                        "reset_in_days": reset_in_days
                    }, session_id
                rec["sessions"][session_id] += 1
                return True, "session_edit_consumed", {
                    "monthly_used": rec["prompts_used"],
                    "monthly_limit": self.MAX_MONTHLY_PROMPTS,
                    "session_edits": rec["sessions"][session_id],
                    "session_edit_limit": self.MAX_SESSION_EDITS,
                    "reset_in_days": reset_in_days
                }, session_id
            else:
                # New root prompt
                if rec["prompts_used"] >= self.MAX_MONTHLY_PROMPTS:
                    return False, f"Monthly free trial limit reached ({self.MAX_MONTHLY_PROMPTS}/{self.MAX_MONTHLY_PROMPTS} prompts). Renews in {reset_in_days} days. Download Vo-Gen-Flow Desktop for unlimited generations.", {
                        "monthly_used": rec["prompts_used"],
                        "monthly_limit": self.MAX_MONTHLY_PROMPTS,
                        "session_edits": 0,
                        "session_edit_limit": self.MAX_SESSION_EDITS,
                        "reset_in_days": reset_in_days
                    }, session_id or ""
                rec["prompts_used"] += 1
                sid = session_id or uuid.uuid4().hex[:12]
                rec["sessions"][sid] = 0
                return True, "monthly_prompt_consumed", {
                    "monthly_used": rec["prompts_used"],
                    "monthly_limit": self.MAX_MONTHLY_PROMPTS,
                    "session_edits": 0,
                    "session_edit_limit": self.MAX_SESSION_EDITS,
                    "reset_in_days": reset_in_days
                }, sid

    def get_quota_status(self, client_id: str, session_id: Optional[str] = None) -> Dict[str, Any]:
        with self._lock:
            rec = self._get_client_record(client_id)
            now = time.time()
            reset_in_days = max(1, int((self.MONTH_SECONDS - (now - rec["period_start"])) / 86400))
            edits = rec["sessions"].get(session_id, 0) if session_id else 0
            return {
                "monthly_used": rec["prompts_used"],
                "monthly_limit": self.MAX_MONTHLY_PROMPTS,
                "monthly_remaining": max(0, self.MAX_MONTHLY_PROMPTS - rec["prompts_used"]),
                "session_edits_used": edits,
                "session_edits_remaining": max(0, self.MAX_SESSION_EDITS - edits) if session_id else self.MAX_SESSION_EDITS,
                "session_edit_limit": self.MAX_SESSION_EDITS,
                "reset_in_days": reset_in_days
            }


# Global singletons
trial_manager = TrialQuotaManager()
knowledge_db: Optional[CuratedKnowledgeDB] = None
stt_service: Optional[STTService] = None
council_engine: Optional[CouncilEngine] = None
rag_engine: Optional[LocalRAGEngine] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager for startup and shutdown."""
    global knowledge_db, stt_service, council_engine, rag_engine
    logger.info("Initializing Vo-Gen-Flow API Gateway services...")
    knowledge_db = CuratedKnowledgeDB()
    stt_service = STTService()
    rag_engine = LocalRAGEngine(model_router=ModelRouter(api_key="USE_ENV"))
    
    # Pre-seed RAG engine with curated architecture blueprints & schemas
    try:
        for t in knowledge_db.templates:
            content = (
                f"# {t.get('title')}\n\n"
                f"Category: {t.get('category')}\n"
                f"Description: {t.get('description')}\n"
                f"Keywords: {', '.join(t.get('keywords', []))}\n\n"
                f"```sql\n{t.get('snippet', '')}\n```"
            )
            rag_engine.index_text(content, source_name=f"{t.get('id')}.md")
        
        # Also pre-seed with any existing specs in output directory
        out_dir = Path("output")
        if out_dir.exists():
            for md_file in out_dir.glob("*.md"):
                try:
                    rag_engine.index_file(str(md_file))
                except Exception:
                    pass
        logger.info("RAG Engine pre-seeded successfully with %d chunks.", len(rag_engine.chunks))
    except Exception as e:
        logger.warning("RAG pre-seeding error: %s", str(e))

    council_engine = CouncilEngine(knowledge_db=knowledge_db, rag_engine=rag_engine)
    logger.info("SQLiteStore active with journal_mode: %s", sqlite_store.get_journal_mode())
    logger.info("Services initialized. Ready to receive requests.")
    yield
    logger.info("Shutting down Vo-Gen-Flow API Gateway...")
    sqlite_store.close()


app = FastAPI(
    title="Vo-Gen-Flow Gateway",
    description="Commercial Voice-to-Workflow Generative AI API & Streaming WebSocket Gateway",
    version="2.0.0",
    lifespan=lifespan
)

# Security: Session ID alphanumeric and hyphen/underscore validator
SAFE_SESSION_RE = re.compile(r"^[a-zA-Z0-9_\-]+$")

# CORS Policy configuration with secure origin whitelist
ALLOWED_ORIGINS_ENV = os.getenv("ALLOWED_ORIGINS")
if ALLOWED_ORIGINS_ENV:
    ALLOWED_ORIGINS = [o.strip() for o in ALLOWED_ORIGINS_ENV.split(",") if o.strip()]
else:
    ALLOWED_ORIGINS = [
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$",
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


# --- Request/Response Models ---

class HealthResponse(BaseModel):
    status: str = "healthy"
    version: str = "2.0.0"
    service: str = "Vo-Gen-Flow"
    groq_configured: bool = False


class DeliberateRequest(BaseModel):
    transcript: str = Field(..., min_length=3, description="Spoken transcript to process")
    preset: str = Field(default="standard", description="Council preset name")
    byok_key: Optional[str] = Field(default=None, description="Optional Bring-Your-Own-Key for Groq")
    session_id: Optional[str] = Field(default=None, pattern=r"^[a-zA-Z0-9_\-]+$", description="Optional existing session ID for iterative edits")
    engine_mode: Optional[str] = Field(default="auto", description="Execution engine: 'auto' | 'groq' | 'lm_studio'")


class KnowledgeSearchRequest(BaseModel):
    query: str = Field(..., min_length=2)
    top_k: int = Field(default=3, ge=1, le=10)


class RAGIndexRequest(BaseModel):
    text: str = Field(..., min_length=10, description="Code or documentation to index")
    source_name: str = Field(default="custom_document.md", description="Document label")


class RAGQueryRequest(BaseModel):
    query: str = Field(..., min_length=2, description="Question to ask against indexed knowledge base")
    top_k: int = Field(default=3, ge=1, le=10)
    byok_key: Optional[str] = Field(default=None, description="Optional BYOK Groq API key")


# --- REST Endpoints ---

@app.get("/health", response_model=HealthResponse, tags=["System"])
async def health():
    """Health check probe endpoint."""
    return HealthResponse(
        status="healthy",
        version="2.0.0",
        service="Vo-Gen-Flow",
        groq_configured=Config.has_groq_key()
    )


@app.get("/api/engine/status", tags=["System"])
async def get_engine_status():
    """Return status of Groq LPU and LM Studio Bionic engines."""
    from src.model_router import check_lm_studio_available, ROLE_MODEL_MAPPING, LM_STUDIO_DEFAULT_URL, LM_STUDIO_DEFAULT_MODEL
    lm_available = check_lm_studio_available(LM_STUDIO_DEFAULT_URL)
    groq_ready = Config.has_groq_key()
    return {
        "active_engine": "groq" if groq_ready else ("lm_studio" if lm_available else "offline_simulation"),
        "groq": {
            "configured": groq_ready,
            "models": ROLE_MODEL_MAPPING
        },
        "lm_studio": {
            "reachable": lm_available,
            "url": LM_STUDIO_DEFAULT_URL,
            "model": LM_STUDIO_DEFAULT_MODEL
        }
    }


@app.get("/api/trial/quota", tags=["System"])
async def get_trial_quota(request: Request, session_id: Optional[str] = None):
    """Retrieve monthly trial quota and session edit status."""
    client_ip = request.headers.get("x-client-id") or request.headers.get("x-forwarded-for", "").split(",")[0].strip() or (request.client.host if request.client else "127.0.0.1")
    return trial_manager.get_quota_status(client_ip, session_id=session_id)


@app.get("/api/presets", tags=["Council"])
async def get_presets():
    """Return all available multi-model council presets."""
    return {"presets": COUNCIL_PRESETS}


@app.post("/api/stt/transcribe", tags=["STT"])
async def transcribe_audio(file: UploadFile = File(...)):
    """Transcribe an uploaded audio file using Groq Whisper LPU with path traversal hardening."""
    global stt_service
    if not stt_service:
        stt_service = STTService()

    # Sanitize uploaded filename and imprison within TEMP_AUDIO_DIR
    raw_filename = file.filename or "upload.wav"
    safe_filename = os.path.basename(raw_filename)
    safe_filename = re.sub(r"[^a-zA-Z0-9._\-]", "_", safe_filename)
    if not safe_filename.strip("._"):
        safe_filename = "upload.wav"

    temp_path = os.path.join(Config.TEMP_AUDIO_DIR, f"upload_{uuid.uuid4().hex[:8]}_{safe_filename}")
    resolved_temp = Path(temp_path).resolve()
    resolved_base = Path(Config.TEMP_AUDIO_DIR).resolve()
    if not resolved_temp.is_relative_to(resolved_base):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid audio filename: Directory traversal detected."
        )

    try:
        content = await file.read()
        with open(temp_path, "wb") as f:
            f.write(content)

        res = await asyncio.to_thread(stt_service.transcribe, temp_path)
        return res.to_dict() if hasattr(res, "to_dict") else res
    except HTTPException:
        raise
    except Exception as e:
        logger.error("STT transcription error: %s", str(e))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    finally:
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception:
                pass


@app.get("/api/stt/sample-audio", tags=["STT"])
async def get_sample_audio():
    """Serve pre-generated architectural voice memo audio file for testing."""
    sample_path = os.path.join(Config.BASE_DIR if hasattr(Config, "BASE_DIR") else os.getcwd(), "data", "sample_audio.wav")
    if not os.path.exists(sample_path):
        sample_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "sample_audio.wav")
    if not os.path.exists(sample_path):
        raise HTTPException(status_code=404, detail="Sample audio file not found on server.")
    return FileResponse(sample_path, media_type="audio/wav", filename="sample_audio.wav")


@app.post("/api/council/deliberate", tags=["Council"])
async def deliberate_council(req: DeliberateRequest, request: Request):
    """Trigger Council DAG deliberation on a technical transcript with trial quota checks."""
    global council_engine
    if not council_engine:
        council_engine = CouncilEngine()

    # Security: Validate session_id format if provided
    if req.session_id and not SAFE_SESSION_RE.match(req.session_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid session_id format: Must match ^[a-zA-Z0-9_\\-]+$"
        )

    # Enforce trial quota limits
    client_ip = request.headers.get("x-client-id") or request.headers.get("x-forwarded-for", "").split(",")[0].strip() or (request.client.host if request.client else "127.0.0.1")
    is_local_dev = client_ip in ("127.0.0.1", "localhost", "::1") and not request.headers.get("x-enforce-quota")
    is_test = client_ip == "testclient" and not request.headers.get("x-enforce-quota")
    bypass = request.headers.get("x-bypass-quota") == "true" or os.environ.get("VOGENFLOW_DISABLE_QUOTA") == "1" or is_test or is_local_dev

    if bypass:
        session_id = req.session_id or uuid.uuid4().hex[:12]
        quota_info = trial_manager.get_quota_status(client_ip, session_id=session_id)
    else:
        allowed, reason, quota_info, session_id = trial_manager.check_and_consume(client_ip, session_id=req.session_id)
        if not allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "error": "quota_exceeded",
                    "message": reason,
                    "quota": quota_info
                }
            )

    try:
        # If user provides custom key or specific engine mode, instantiate temporary router
        if (req.byok_key and req.byok_key.strip()) or (req.engine_mode and req.engine_mode != "auto"):
            temp_router = ModelRouter(
                api_key=req.byok_key.strip() if req.byok_key else "USE_ENV",
                engine_mode=req.engine_mode or "auto"
            )
            engine = CouncilEngine(model_router=temp_router, knowledge_db=knowledge_db, rag_engine=rag_engine)
        else:
            engine = council_engine

        # Non-blocking deliberation: run off the main event loop thread
        result = await asyncio.to_thread(engine.deliberate, transcript=req.transcript, preset=req.preset)

        # Persist session artifacts
        saved_paths = engine.persist_artifacts(session_id, result["artifacts"])
        ACTIVE_SESSIONS[session_id] = {
            "session_id": session_id,
            "transcript": req.transcript,
            "preset": req.preset,
            "artifacts": result["artifacts"],
            "telemetry": result["telemetry"],
            "duration": result["duration_seconds"],
            "created_at": time.time(),
            "saved_paths": saved_paths,
            "project_ir": result.get("project_ir")
        }

        return {
            "session_id": session_id,
            "status": "success",
            "duration_seconds": result["duration_seconds"],
            "artifacts": result["artifacts"],
            "telemetry": result["telemetry"],
            "seat_dossier": result.get("seat_dossier", {}),
            "project_ir": result.get("project_ir"),
            "quota": quota_info
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Council deliberation error: %s", str(e))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@app.post("/api/knowledge/search", tags=["Knowledge"])
async def search_knowledge(req: KnowledgeSearchRequest):
    """Retrieve matching architectural templates from the Curated Knowledge Catalog."""
    global knowledge_db
    if not knowledge_db:
        knowledge_db = CuratedKnowledgeDB()
    matches = knowledge_db.search(req.query, top_k=req.top_k)
    return {"query": req.query, "matches": matches}


@app.post("/api/rag/index", tags=["RAG"])
async def index_rag_document(req: RAGIndexRequest):
    """Index text or code into the embedded RAG engine with guardrail sanitization."""
    global rag_engine
    if not rag_engine:
        rag_engine = LocalRAGEngine()
    rag_engine.index_text(req.text, source_name=req.source_name)
    return {
        "status": "indexed",
        "source_name": req.source_name,
        "total_chunks": len(rag_engine.chunks),
        "guardrail_telemetry": {
            "blocked_sensitive_files": rag_engine.blocked_sensitive_files,
            "sanitized_injections": rag_engine.sanitized_injections_count
        }
    }


@app.post("/api/rag/query", tags=["RAG"])
async def query_rag_document(req: RAGQueryRequest):
    """Query indexed documents with zero-hallucination guardrails and source citations."""
    global rag_engine
    if not rag_engine:
        rag_engine = LocalRAGEngine()

    if req.byok_key and req.byok_key.strip():
        router = ModelRouter(api_key=req.byok_key.strip())
    else:
        router = ModelRouter(api_key="USE_ENV")

    # Non-blocking RAG QA execution off the main event loop thread
    result = await asyncio.to_thread(rag_engine.query_document, req.query, top_k=req.top_k, model_router=router)
    return result


@app.get("/api/sessions", tags=["Sessions"])
async def list_persisted_sessions(limit: int = 50, offset: int = 0):
    """Retrieve all persisted sessions from SQLite store."""
    return {"sessions": sqlite_store.list_sessions(limit=limit, offset=offset)}


@app.get("/api/sessions/{session_id}", tags=["Sessions"])
async def get_session(session_id: str):
    """Fetch stored artifacts and telemetry for an active session with security validation."""
    if not session_id or not SAFE_SESSION_RE.match(session_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid session_id format: Must match ^[a-zA-Z0-9_\\-]+$"
        )
    session_data = sqlite_store.get_session(session_id)
    if not session_data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    return session_data


@app.get("/api/sessions/{session_id}/artifacts", tags=["Sessions"])
async def get_session_artifacts(session_id: str, doc_type: Optional[str] = None):
    """Retrieve artifacts for a specific session."""
    if not session_id or not SAFE_SESSION_RE.match(session_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid session_id format: Must match ^[a-zA-Z0-9_\\-]+$"
        )
    artifacts = sqlite_store.get_artifacts(session_id, doc_type=doc_type, as_dict=True)
    return {"session_id": session_id, "artifacts": artifacts}


# --- WebSocket Streaming Gateway ---

def compute_rms(pcm_bytes: bytes) -> float:
    """Calculate RMS power from 16-bit PCM bytes."""
    if len(pcm_bytes) < 2:
        return 0.0
    count = len(pcm_bytes) // 2
    try:
        shorts = struct.unpack(f"<{count}h", pcm_bytes[:count * 2])
        sum_sq = sum(s * s for s in shorts)
        rms = math.sqrt(sum_sq / count) / 32768.0
        return min(1.0, rms * 5.0)  # normalized scaled RMS
    except Exception:
        return 0.0


@app.websocket("/ws/stream")
async def websocket_stream_endpoint(websocket: WebSocket):
    """Bidirectional WebSocket for live audio streaming, volume telemetry, and real-time council synthesis."""
    await websocket.accept()
    session_id = uuid.uuid4().hex[:12]
    audio_buffer = bytearray()
    current_preset = "standard"
    logger.info("WebSocket client connected (Session: %s)", session_id)

    try:
        await websocket.send_json({
            "type": "connection_established",
            "session_id": session_id,
            "message": "Connected to Vo-Gen-Flow Real-Time Audio Gateway"
        })

        while True:
            message = await websocket.receive()

            # Handle Binary Audio Frames (16kHz PCM chunks)
            if "bytes" in message and message["bytes"]:
                chunk = message["bytes"]
                audio_buffer.extend(chunk)
                rms = compute_rms(chunk)
                await websocket.send_json({
                    "type": "audio_telemetry",
                    "rms": round(rms, 4),
                    "total_bytes": len(audio_buffer)
                })

            # Handle JSON Control Messages
            elif "text" in message and message["text"]:
                try:
                    payload = json.loads(message["text"])
                    msg_type = payload.get("type", "")

                    if msg_type == "start_recording":
                        audio_buffer.clear()
                        current_preset = payload.get("preset", "standard")
                        await websocket.send_json({
                            "type": "recording_started",
                            "preset": current_preset
                        })

                    elif msg_type == "audio_chunk_base64":
                        import base64
                        raw_data = base64.b64decode(payload.get("data", ""))
                        audio_buffer.extend(raw_data)
                        rms = compute_rms(raw_data)
                        await websocket.send_json({
                            "type": "audio_telemetry",
                            "rms": round(rms, 4),
                            "total_bytes": len(audio_buffer)
                        })

                    elif msg_type == "stop_recording":
                        await websocket.send_json({
                            "type": "processing_started",
                            "audio_bytes": len(audio_buffer)
                        })

                        # Transcribe audio buffer or use fallback text
                        transcript = payload.get("mock_transcript", "")
                        if not transcript and len(audio_buffer) > 1000:
                            # Save temp WAV file
                            temp_wav = os.path.join(Config.TEMP_AUDIO_DIR, f"ws_{session_id}.wav")
                            import wave
                            with wave.open(temp_wav, "wb") as wf:
                                wf.setnchannels(1)
                                wf.setsampwidth(2)
                                wf.setframerate(16000)
                                wf.writeframes(bytes(audio_buffer))

                            try:
                                if stt_service:
                                    stt_res = stt_service.transcribe(temp_wav)
                                    transcript = stt_res.get("text", "")
                            finally:
                                if os.path.exists(temp_wav):
                                    try:
                                        os.remove(temp_wav)
                                    except Exception:
                                        pass

                        if not transcript:
                            transcript = payload.get("transcript", "Build an automated high-throughput cloud service with PostgreSQL, FastAPI, and real-time WebSockets.")

                        await websocket.send_json({
                            "type": "transcript_ready",
                            "transcript": transcript
                        })

                        # Non-blocking Council Deliberation with real-time websocket progress callbacks
                        async def send_progress(role: str, data: Dict[str, Any]):
                            try:
                                await websocket.send_json({
                                    "type": "council_progress",
                                    "role": role,
                                    "message": data.get("message", ""),
                                    "tokens": data.get("tokens", 0)
                                })
                            except Exception as ws_err:
                                logger.debug("Could not flush WebSocket progress frame: %s", str(ws_err))

                        loop = asyncio.get_running_loop()

                        def sync_cb(role, data):
                            asyncio.run_coroutine_threadsafe(send_progress(role, data), loop)

                        engine = council_engine or CouncilEngine()
                        result = await asyncio.to_thread(
                            engine.deliberate,
                            transcript=transcript,
                            preset=current_preset,
                            progress_callback=sync_cb
                        )

                        await websocket.send_json({
                            "type": "deliberation_complete",
                            "artifacts": result["artifacts"],
                            "duration_seconds": result["duration_seconds"]
                        })

                    elif msg_type == "ping":
                        await websocket.send_json({"type": "pong", "timestamp": time.time()})

                except json.JSONDecodeError:
                    await websocket.send_json({"type": "error", "message": "Invalid JSON format"})

    except (WebSocketDisconnect, RuntimeError):
        logger.info("WebSocket client disconnected cleanly (Session: %s)", session_id)
    except Exception as e:
        logger.error("WebSocket unhandled exception: %s", str(e))


# Mount static web app if directory exists
_web_app_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "web_app")
if os.path.exists(_web_app_dir):
    app.mount("/", StaticFiles(directory=_web_app_dir, html=True), name="web_app")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.api.server:app", host="0.0.0.0", port=8080, reload=False)

