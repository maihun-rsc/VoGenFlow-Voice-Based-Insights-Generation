"""FastAPI REST & WebSocket Gateway Server for Vo-Gen-Flow."""

import os
import json
import time
import uuid
import math
import struct
import logging
from typing import Dict, Any, Optional, List
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, UploadFile, File, Form, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from src.config import Config
from src.stt_service import STTService
from src.knowledge_db import CuratedKnowledgeDB
from src.model_router import ModelRouter
from src.council_engine import CouncilEngine, COUNCIL_PRESETS

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("vogenflow.api")

# In-memory session store
ACTIVE_SESSIONS: Dict[str, Dict[str, Any]] = {}

# Global singletons
knowledge_db: Optional[CuratedKnowledgeDB] = None
stt_service: Optional[STTService] = None
council_engine: Optional[CouncilEngine] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager for startup and shutdown."""
    global knowledge_db, stt_service, council_engine
    logger.info("Initializing Vo-Gen-Flow API Gateway services...")
    knowledge_db = CuratedKnowledgeDB()
    stt_service = STTService()
    council_engine = CouncilEngine(knowledge_db=knowledge_db)
    logger.info("Services initialized. Ready to receive requests.")
    yield
    logger.info("Shutting down Vo-Gen-Flow API Gateway...")


app = FastAPI(
    title="Vo-Gen-Flow Gateway",
    description="Commercial Voice-to-Workflow Generative AI API & Streaming WebSocket Gateway",
    version="2.0.0",
    lifespan=lifespan
)

# CORS Policy configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
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


class KnowledgeSearchRequest(BaseModel):
    query: str = Field(..., min_length=2)
    top_k: int = Field(default=3, ge=1, le=10)


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


@app.get("/api/presets", tags=["Council"])
async def get_presets():
    """Return all available multi-model council presets."""
    return {"presets": COUNCIL_PRESETS}


@app.post("/api/stt/transcribe", tags=["STT"])
async def transcribe_audio(file: UploadFile = File(...)):
    """Transcribe an uploaded audio file using Groq Whisper LPU."""
    global stt_service
    if not stt_service:
        stt_service = STTService()

    # Save to temp file
    temp_path = os.path.join(Config.TEMP_AUDIO_DIR, f"upload_{uuid.uuid4().hex[:8]}_{file.filename}")
    try:
        content = await file.read()
        with open(temp_path, "wb") as f:
            f.write(content)

        res = stt_service.transcribe(temp_path)
        return res
    except Exception as e:
        logger.error("STT transcription error: %s", str(e))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    finally:
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception:
                pass


@app.post("/api/council/deliberate", tags=["Council"])
async def deliberate_council(req: DeliberateRequest):
    """Trigger Council DAG deliberation on a technical transcript."""
    global council_engine
    if not council_engine:
        council_engine = CouncilEngine()

    try:
        # If user provides a custom BYOK key, instantiate a temporary router
        if req.byok_key and req.byok_key.strip():
            temp_router = ModelRouter(api_key=req.byok_key.strip())
            engine = CouncilEngine(model_router=temp_router, knowledge_db=knowledge_db)
        else:
            engine = council_engine

        result = engine.deliberate(transcript=req.transcript, preset=req.preset)

        # Store in active session
        session_id = uuid.uuid4().hex[:12]
        saved_paths = engine.persist_artifacts(session_id, result["artifacts"])
        ACTIVE_SESSIONS[session_id] = {
            "session_id": session_id,
            "transcript": req.transcript,
            "preset": req.preset,
            "artifacts": result["artifacts"],
            "telemetry": result["telemetry"],
            "duration": result["duration_seconds"],
            "created_at": time.time(),
            "saved_paths": saved_paths
        }

        return {
            "session_id": session_id,
            "status": "success",
            "duration_seconds": result["duration_seconds"],
            "artifacts": result["artifacts"],
            "telemetry": result["telemetry"]
        }
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


@app.get("/api/sessions/{session_id}", tags=["Sessions"])
async def get_session(session_id: str):
    """Fetch stored artifacts and telemetry for an active session."""
    if session_id not in ACTIVE_SESSIONS:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    return ACTIVE_SESSIONS[session_id]


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

                        # Execute Council Deliberation with real-time websocket progress callbacks
                        async def send_progress(role: str, data: Dict[str, Any]):
                            await websocket.send_json({
                                "type": "council_progress",
                                "role": role,
                                "message": data.get("message", ""),
                                "tokens": data.get("tokens", 0)
                            })

                        # Sync wrapper for progress
                        import asyncio
                        loop = asyncio.get_event_loop()

                        def sync_cb(role, data):
                            loop.create_task(send_progress(role, data))

                        engine = council_engine or CouncilEngine()
                        result = engine.deliberate(
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.api.server:app", host="0.0.0.0", port=8000, reload=False)
