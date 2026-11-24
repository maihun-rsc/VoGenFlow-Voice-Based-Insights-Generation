"""
tests/integration/test_websocket_stream.py
Tier 2: Real Integration & Contract Test Suite for WebSocket Streaming Gateway.

Validates /ws/stream bidirectional communication:
- Initial connection handshake & session generation
- Ping/pong heartbeat telemetry
- Binary audio PCM streaming & RMS calculation
- Base64 audio chunk streaming
- Lifecycle state transitions (start_recording, stop_recording)
- Real-time council progress streaming via non-blocking callbacks
- Deliberation artifact delivery
- Error handling on invalid JSON payloads
"""

import json
import struct
import base64
import pytest
from fastapi.testclient import TestClient
from src.api.server import app


@pytest.fixture(scope="module")
def client():
    """Create a TestClient with lifespan context manager."""
    with TestClient(app) as c:
        yield c


@pytest.mark.integration
class TestWebSocketStreaming:
    """Rigorous integration tests for the /ws/stream WebSocket gateway."""

    def test_connection_handshake(self, client):
        """Verify WebSocket handshake delivers session ID and welcome payload."""
        with client.websocket_connect("/ws/stream") as ws:
            data = ws.receive_json()
            assert data["type"] == "connection_established"
            assert "session_id" in data
            assert len(data["session_id"]) >= 8
            assert "Vo-Gen-Flow" in data["message"]

    def test_ping_pong_heartbeat(self, client):
        """Verify client ping triggers immediate pong with timestamp."""
        with client.websocket_connect("/ws/stream") as ws:
            ws.receive_json()  # Consume connection_established
            ws.send_text(json.dumps({"type": "ping"}))
            data = ws.receive_json()
            assert data["type"] == "pong"
            assert "timestamp" in data
            assert isinstance(data["timestamp"], (int, float))

    def test_binary_pcm_streaming_and_rms_telemetry(self, client):
        """Verify binary 16kHz PCM audio chunks return real-time RMS telemetry."""
        with client.websocket_connect("/ws/stream") as ws:
            ws.receive_json()  # connection_established

            # Generate synthetic 16-bit PCM audio samples (sine wave or pulses)
            num_samples = 160
            pcm_data = struct.pack(f"<{num_samples}h", *([8000] * num_samples))

            ws.send_bytes(pcm_data)
            data = ws.receive_json()

            assert data["type"] == "audio_telemetry"
            assert "rms" in data
            assert data["rms"] > 0.0
            assert data["total_bytes"] == len(pcm_data)

    def test_base64_audio_chunk_telemetry(self, client):
        """Verify base64 audio frames update buffer and compute valid RMS."""
        with client.websocket_connect("/ws/stream") as ws:
            ws.receive_json()  # connection_established

            raw_pcm = struct.pack("<100h", *([4000] * 100))
            b64_str = base64.b64encode(raw_pcm).decode("utf-8")

            ws.send_text(json.dumps({
                "type": "audio_chunk_base64",
                "data": b64_str
            }))

            data = ws.receive_json()
            assert data["type"] == "audio_telemetry"
            assert data["rms"] > 0.0
            assert data["total_bytes"] == len(raw_pcm)

    def test_recording_lifecycle_and_council_deliberation(self, client):
        """Verify full recording lifecycle and non-blocking council progress delivery."""
        with client.websocket_connect("/ws/stream") as ws:
            ws.receive_json()  # connection_established

            # 1. Start recording
            ws.send_text(json.dumps({
                "type": "start_recording",
                "preset": "lean_sprint"
            }))
            rec_start = ws.receive_json()
            assert rec_start["type"] == "recording_started"
            assert rec_start["preset"] == "lean_sprint"

            # 2. Stream audio bytes
            raw_pcm = struct.pack("<200h", *([6000] * 200))
            ws.send_bytes(raw_pcm)
            telemetry = ws.receive_json()
            assert telemetry["type"] == "audio_telemetry"

            # 3. Stop recording with explicit transcript
            test_transcript = "Build a lightweight microservice with FastAPI and SQLite for order processing."
            ws.send_text(json.dumps({
                "type": "stop_recording",
                "transcript": test_transcript
            }))

            # Expect processing_started
            proc_started = ws.receive_json()
            assert proc_started["type"] == "processing_started"

            # Expect transcript_ready
            tx_ready = ws.receive_json()
            assert tx_ready["type"] == "transcript_ready"
            assert tx_ready["transcript"] == test_transcript

            # Expect council_progress events followed by deliberation_complete
            progress_events = []
            deliberation_complete = None

            # Collect streaming messages until complete or timeout
            for _ in range(20):
                msg = ws.receive_json()
                if msg["type"] == "council_progress":
                    progress_events.append(msg)
                    assert "role" in msg
                elif msg["type"] == "deliberation_complete":
                    deliberation_complete = msg
                    break

            assert len(progress_events) >= 1, "Expected at least 1 real-time council progress event"
            assert deliberation_complete is not None, "Did not receive deliberation_complete message"
            assert "artifacts" in deliberation_complete
            assert "PRD.md" in deliberation_complete["artifacts"]
            assert "master_execution_bundle.md" in deliberation_complete["artifacts"]
            assert deliberation_complete["duration_seconds"] > 0

    def test_invalid_json_error_handling(self, client):
        """Verify malformed JSON over WebSocket returns structured error without disconnecting."""
        with client.websocket_connect("/ws/stream") as ws:
            ws.receive_json()  # connection_established

            # Send invalid raw JSON
            ws.send_text("{malformed: json, missing quotes}")
            data = ws.receive_json()

            assert data["type"] == "error"
            assert "Invalid JSON format" in data["message"]

            # Connection remains open and responsive to valid frames
            ws.send_text(json.dumps({"type": "ping"}))
            pong = ws.receive_json()
            assert pong["type"] == "pong"
