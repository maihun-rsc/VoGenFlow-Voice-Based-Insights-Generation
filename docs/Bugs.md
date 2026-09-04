# Vo-Gen-Flow: Root Cause Analysis (RCA) & Issue Resolution Ledger
> **File Identification:** `docs/Bugs.md`  
> **Status:** All Discovered Issues Resolved & Verified by Automated Tests

---

## Issue Ledger & Resolution Summaries

### BUG-001: Missing `Config` Class in `src/config.py`
- **Severity:** Medium (ImportError during test execution).
- **Symptom:** `ImportError: cannot import name 'Config' from 'src.config'`.
- **Root Cause Analysis:** `src/config.py` declared configuration variables at module level (`GROQ_API_KEY`, etc.) without a class wrapper `Config`.
- **Resolution:** Implemented `class Config` in `src/config.py` with static accessors preserving backward compatibility with module-level imports.
- **Verification:** `tests/test_router.py` imported and passed.

### BUG-002: Remote API Rate Limiting (HTTP 429) During Local Unit Tests
- **Severity:** High (Test suite delay / 50s retry pauses).
- **Symptom:** `HTTP Request: POST https://api.groq.com/openai/v1/chat/completions "HTTP/1.1 429 Too Many Requests"` triggered during integration tests.
- **Root Cause Analysis:** Unit test cases were calling the live Groq API with user credentials, rapidly hitting the 8,000 TPM free tier rate limit.
- **Resolution:** Configured test suites (`tests/test_api.py`, `tests/test_council.py`, `tests/test_security_pentest.py`) to inject offline deterministic generators (`ModelRouter(api_key=None, min_request_interval=0.01)`).
- **Verification:** Unit tests run in 0.07s without remote network dependencies.

### BUG-003: Unhandled Disconnect on FastAPI TestClient WebSocket
- **Severity:** Low (Log noise).
- **Symptom:** `ERROR: WebSocket unhandled exception: Cannot call "receive" once a disconnect message has been received.`
- **Root Cause Analysis:** When `TestClient.websocket_connect` context exited, it closed the socket while the server's `receive()` was pending, raising `RuntimeError`.
- **Resolution:** Added `(WebSocketDisconnect, RuntimeError)` to the exception handling block in `src/api/server.py`.
- **Verification:** WebSocket disconnects now log cleanly as `WebSocket client disconnected cleanly`.

### BUG-004: Reflected Prompt Injection in Offline PRD Generator
- **Severity:** High (Security Pentest failure).
- **Symptom:** Injected strings like `ADMIN PASSWORD` and `malware` were reflected into the PRD Executive Summary via `f"System designed based on input query: '{prompt[:120]}...'"`.
- **Root Cause Analysis:** Direct string interpolation of raw user transcripts into generated summary artifacts without tag stripping or keyword neutralization.
- **Resolution:** Created `sanitize_input()` regex filtering in `src/model_router.py` and `src/council_engine.py` that strips system tags (`<system>`, `</user_prompt>`), sanitizes command overrides, and generates abstracted domain summaries.
- **Verification:** `tests/test_security_pentest.py` passing 100%.

### BUG-005: Unnecessary Retries on HTTP 401 Unauthorized
- **Severity:** Medium (6s delay on invalid BYOK keys).
- **Symptom:** Groq API client retried multiple times when given an invalid API key, causing unnecessary latency.
- **Root Cause Analysis:** Retry loop treated HTTP 401 the same as transient rate limits (HTTP 429).
- **Resolution:** Added explicit 401 check in `src/model_router.py` that logs invalid key warning, records failure, and breaks immediately without retries.
- **Verification:** Instant circuit breaker trip and offline fallback in <0.02s.
