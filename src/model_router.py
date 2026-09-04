"""Task-Specific Multi-Model Router with Rate Pacing and Circuit Breaker for Vo-Gen-Flow."""

import os
import time
import json
import logging
from typing import Dict, Any, Optional, List
from src.config import Config

logger = logging.getLogger("vogenflow.model_router")

# Task & Council Role to Model Assignment
ROLE_MODEL_MAPPING = {
    "pm_agent": "openai/gpt-oss-120b",
    "architect_agent": "qwen/qwen3.6-27b",
    "ui_agent": "qwen/qwen3.6-27b",
    "systems_agent": "openai/gpt-oss-120b",
    "agile_agent": "qwen/qwen3.6-27b",
    "diff_agent": "openai/gpt-oss-20b",
    "default": "openai/gpt-oss-20b"
}

# Offline / Local Ollama Fallback Model
OLLAMA_FALLBACK_MODEL = "qwen2.5-coder:latest"


class CircuitBreaker:
    """Simple circuit breaker to avoid hammering failing remote APIs."""

    def __init__(self, failure_threshold: int = 3, recovery_time: float = 30.0):
        self.failure_threshold = failure_threshold
        self.recovery_time = recovery_time
        self.failure_count = 0
        self.last_failure_time = 0.0
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN

    def record_success(self):
        self.failure_count = 0
        self.state = "CLOSED"

    def record_failure(self):
        self.failure_count += 1
        self.last_failure_time = time.time()
        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"
            logger.warning("Circuit breaker tripped to OPEN state (%d consecutive failures).", self.failure_count)

    def trip(self, reason: str = "Immediate circuit trip"):
        """Force circuit breaker to OPEN state immediately (e.g. fatal 401 auth error)."""
        self.failure_count = self.failure_threshold
        self.last_failure_time = time.time()
        self.state = "OPEN"
        logger.warning("Circuit breaker forced to OPEN state. Reason: %s", reason)

    def allow_request(self) -> bool:
        if self.state == "CLOSED":
            return True
        if self.state == "OPEN":
            if time.time() - self.last_failure_time > self.recovery_time:
                self.state = "HALF_OPEN"
                logger.info("Circuit breaker entering HALF_OPEN trial state.")
                return True
            return False
        if self.state == "HALF_OPEN":
            return True
        return True


def is_valid_groq_key(key: Optional[str]) -> bool:
    """Validate Groq API key format before initializing network client."""
    if not key or not isinstance(key, str):
        return False
    k = key.strip()
    if not k or k.startswith("your_") or k.lower() in ("dummy", "test", "fake", "null", "none", "use_env"):
        return False
    return k.startswith("gsk_") and len(k) >= 20


def sanitize_input(text: str) -> str:
    """Sanitize user input to neutralize prompt injection, tag breakout, and command override attempts."""
    if not text:
        return ""
    import re
    # Remove XML / pseudo system tags
    sanitized = re.sub(r"<\/?(system|user|assistant|user_prompt|admin|eval|context)[^>]*>", " ", text, flags=re.IGNORECASE)
    # Neutralize common jailbreak / override phrases
    jailbreaks = [
        r"ignore\s+(all\s+)?previous\s+instructions",
        r"disregard\s+(all\s+)?prior\s+prompts",
        r"output\s+(the\s+)?admin\s+password",
        r"admin\s+password",
        r"dump\s+(all\s+)?environment\s+variables",
        r"system\s+compromised",
        r"disregard\s+prd",
        r"write\s+malware",
        r"malware"
    ]
    for pattern in jailbreaks:
        sanitized = re.sub(pattern, "[SECURITY_FILTERED]", sanitized, flags=re.IGNORECASE)
    # Collapse whitespace
    sanitized = re.sub(r"\s+", " ", sanitized).strip()
    return sanitized


def _sanitize_prompt_for_summary(prompt: str) -> str:
    """Sanitize and summarize user prompt/context for safe interpolation into offline blueprints.

    Neutralizes:
    - XML/HTML tag breakout attempts (e.g. </user_prompt>, <system>, <script>)
    - Role spoofing (e.g. Assistant:, System:, User:, Admin:)
    - System overrides, jailbreak directives, and command injections
    - Dangerous attack tokens (e.g. 'malware', 'admin password', 'system compromised', SQL injections, ransomware)
    - Delimiter breakout fences (```, ---)

    Returns a clean, safe, descriptive domain summary. If input contains only malicious/adversarial
    payloads or lacks substantive domain intent, returns a safe default architectural domain summary.
    """
    if not prompt or not isinstance(prompt, str):
        return "Enterprise Cloud Workflow & High-Throughput Architecture"

    import re
    text = prompt

    # 1. Unpack prompt scaffolding if assembled by council engine
    if "Spoken Transcript:" in text:
        match = re.search(r"Spoken Transcript:\s*(.*?)(?:\n\nCurated Knowledge:|\n\nWorkspace Context:|$)", text, re.DOTALL)
        if match:
            text = match.group(1).strip()
    elif "PRD Context:" in text:
        match = re.search(r"PRD Context:\s*(.*?)(?:\n\nReference Architecture Snippet:|$)", text, re.DOTALL)
        if match:
            text = match.group(1).strip()
    elif "Council Artifacts Summary:" in text:
        match = re.search(r"### PRD\.md\s*(.*?)(?:\n### |$)", text, re.DOTALL)
        if match:
            text = match.group(1).strip()

    # 2. Strip XML/HTML tags (delimiter breakout protection)
    text = re.sub(r"</?[a-zA-Z0-9_\:\-]+[^>]*>", " ", text)

    # 3. Strip markdown code fences, headers, and horizontal delimiter rules
    text = re.sub(r"```[\w]*", " ", text)
    text = re.sub(r"^\s*[-=_*#]{2,}\s*$", " ", text, flags=re.MULTILINE)

    # 4. Strip role impersonation prefixes
    text = re.sub(r"\b(?:Assistant|System|User|Admin|Human|AI|Operator|Root)\s*:\s*", " ", text, flags=re.IGNORECASE)

    # 5. Targeted neutralization of jailbreak/injection directives & harmful keywords
    threat_patterns = [
        r"\b(?:ignore|disregard|forget|bypass|override)\s+(?:all\s+)?(?:previous|prior|system|safety|security)?\s*(?:instructions?|prompts?|rules?|guardrails?|prd)?\b",
        r"\bdisregard\s+(?:the\s+)?prd\b",
        r"\bsystem\s+(?:compromised|override|failure|halt|reboot|shutdown)\b",
        r"\bsecurity\s+override\b",
        r"\b(?:write|create|generate|distribute|execute|deploy|install)\s+(?:malware|ransomware|spyware|trojan|virus|exploit|backdoor|rootkit)\b",
        r"\b(?:malware|ransomware|spyware|trojan|rootkit|keylogger|backdoor|botnet|cryptominer)\b",
        r"\b(?:output|show|print|leak|reveal|dump|exfiltrate|steal)\s+(?:the\s+)?(?:admin\s+)?(?:passwords?|secrets?|tokens?|credentials?|api[_\s]keys?|private[_\s]keys?|env(?:ironment)?\s+vars?)\b",
        r"\badmin\s+passwords?\b",
        r"\bmaster\s+passwords?\b",
        r"\broot\s+passwords?\b",
        r"\bdump\s+(?:all\s+)?(?:environment\s+variables|env\s+vars?|secrets?|database|tables?)\b",
        r"\b(?:dump|reveal|leak|exfiltrate)\s+(?:all\s+)?(?:and\s+)?(?:secrets?|passwords?|credentials?)\b",
        r"\b(?:wipe|encrypt|destroy|corrupt)\s+(?:the\s+)?(?:database|disk|hard\s*drive|files?|system)\b",
        r"\bselect\s+\*\s+from\s+\w+\b",
        r"\bdrop\s+(?:table|database|schema)\b",
        r"\bdelete\s+from\s+\w+\b",
        r"\binsert\s+into\s+\w+\b",
        r"\balert\s*\([^\)]*\)",
        r"\b<script\b",
        r"\bxss\b",
    ]
    for pat in threat_patterns:
        text = re.sub(pat, " ", text, flags=re.IGNORECASE)

    # 6. Normalize punctuation & remove dangling conjunctions/prepositions
    text = re.sub(r"[\r\n\t]+", " ", text)
    text = re.sub(r"[^\w\s\-\.,/]", " ", text)
    text = re.sub(r"\s+", " ", text).strip(" -.,;:_")

    text = re.sub(r"^(?:and|or|but|with|to|for|the|a|an)\s+", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s+(?:and|or|but|with|to|for|the|a|an)$", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s*,\s*(?:and|or|but)\s*$", "", text, flags=re.IGNORECASE)
    text = text.strip(" -.,;:_")

    # 7. Check if meaningful legitimate domain keywords remain (>= 2 substantial words)
    words = [
        w for w in re.findall(r"[a-zA-Z]{3,}", text)
        if w.lower() not in {"and", "the", "for", "with", "from", "all", "out", "put", "system", "assistant", "user", "disregard", "provide", "instructions", "deploy"}
    ]
    if len(words) < 2:
        return "Enterprise Cloud Workflow & High-Throughput Architecture"

    # 8. Clean length truncation
    if len(text) > 150:
        truncated = text[:150].rsplit(" ", 1)[0]
        text = truncated + "..."

    return text


class ModelRouter:
    """Routes generation requests to task-specific models on Groq with rate pacing and fallback."""

    def __init__(
        self,
        api_key: Optional[str] = "USE_ENV",
        min_request_interval: float = 2.0,
        offline_mode: Optional[bool] = None,
        max_retries: int = 3,
        retry_backoff: float = 2.0
    ):
        # Resolve offline mode flag
        if offline_mode is not None:
            self.offline_mode = bool(offline_mode)
        else:
            env_val = os.getenv("VOGENFLOW_OFFLINE_MODE", "0").lower()
            self.offline_mode = env_val in ("1", "true", "yes", "on") or getattr(Config, "OFFLINE_MODE", False)

        # Resolve API key
        if api_key == "USE_ENV":
            raw_key = Config.GROQ_API_KEY
        else:
            raw_key = api_key

        # Early key validation
        if raw_key and is_valid_groq_key(raw_key) and not self.offline_mode:
            self.api_key = raw_key.strip()
        else:
            self.api_key = None
            if raw_key and not is_valid_groq_key(raw_key):
                logger.info("Provided Groq API key failed format check. Operating in offline mode.")

        self.min_request_interval = min_request_interval
        self.max_retries = max_retries
        self.retry_backoff = retry_backoff
        self.last_request_time = 0.0
        self.circuit_breaker = CircuitBreaker()
        self.telemetry = {
            "total_calls": 0,
            "total_prompt_tokens": 0,
            "total_completion_tokens": 0,
            "total_latency_seconds": 0.0,
            "errors": 0,
            "calls_per_role": {},
            "calls_per_model": {}
        }
        self.groq_client = None
        if not self.offline_mode and self.api_key:
            self._init_client()
        else:
            logger.info("ModelRouter running in local offline / simulation mode.")

    def _init_client(self):
        """Initialize the Groq client if API key is present."""
        if self.api_key:
            try:
                from groq import Groq
                self.groq_client = Groq(api_key=self.api_key)
                logger.info("Groq API client initialized successfully.")
            except Exception as e:
                logger.warning("Could not initialize Groq client: %s", str(e))
                self.groq_client = None
        else:
            logger.info("No Groq API key configured. Router running in local / simulation mode.")

    def get_model_for_role(self, role: str) -> str:
        """Return the assigned model name for a council role."""
        return ROLE_MODEL_MAPPING.get(role, ROLE_MODEL_MAPPING["default"])

    def _enforce_rate_pacing(self):
        """Ensure at least min_request_interval seconds have elapsed since the last request."""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_request_interval:
            sleep_time = self.min_request_interval - elapsed
            logger.debug("Rate pacing: sleeping for %.2f seconds", sleep_time)
            time.sleep(sleep_time)
        self.last_request_time = time.time()

    def generate(
        self,
        role: str,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.3,
        max_tokens: int = 4096,
        model_override: Optional[str] = None
    ) -> Dict[str, Any]:
        """Execute a text generation request for a specific council role."""
        model = model_override or self.get_model_for_role(role)
        start_time = time.time()
        self.telemetry["total_calls"] += 1
        self.telemetry["calls_per_role"][role] = self.telemetry["calls_per_role"].get(role, 0) + 1
        self.telemetry["calls_per_model"][model] = self.telemetry["calls_per_model"].get(model, 0) + 1

        # Fast-path for explicit offline mode: bypass rate pacing and remote call
        if self.offline_mode:
            return self._fallback_generate(role, model, system_prompt, user_prompt, start_time)

        # Enforce rate-limit pacing for active remote calls or configured pacing
        self._enforce_rate_pacing()

        # Check circuit breaker and client availability
        if not self.groq_client or not self.circuit_breaker.allow_request():
            logger.warning("Bypassing Groq API (Client: %s, CB: %s). Falling back to local offline generator.",
                           bool(self.groq_client), self.circuit_breaker.state)
            return self._fallback_generate(role, model, system_prompt, user_prompt, start_time)

        # Attempt up to max_retries with exponential backoff for HTTP 429
        max_retries = self.max_retries
        backoff = self.retry_backoff
        last_error = None

        for attempt in range(max_retries):
            try:
                response = self.groq_client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                duration = round(time.time() - start_time, 3)
                self.circuit_breaker.record_success()

                content = response.choices[0].message.content or ""
                prompt_tokens = response.usage.prompt_tokens if response.usage else 0
                completion_tokens = response.usage.completion_tokens if response.usage else 0

                self.telemetry["total_prompt_tokens"] += prompt_tokens
                self.telemetry["total_completion_tokens"] += completion_tokens
                self.telemetry["total_latency_seconds"] += duration

                return {
                    "role": role,
                    "model": model,
                    "content": content,
                    "latency_seconds": duration,
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "source": "groq_api",
                    "status": "success"
                }
            except Exception as e:
                err_str = str(e)
                last_error = err_str
                logger.warning("Groq call attempt %d failed for role '%s' on %s: %s", attempt + 1, role, model, err_str)

                # Check for authentication error (401)
                if "401" in err_str or "invalid_api_key" in err_str:
                    logger.warning("Groq authentication failed (401 Invalid Key). Tripping circuit breaker immediately.")
                    self.circuit_breaker.trip("Fatal 401 Invalid Key")
                    self.groq_client = None  # Prevent subsequent attempts with bad key
                    break
                elif "429" in err_str or "rate_limit" in err_str.lower() or "413" in err_str:
                    if attempt < max_retries - 1:
                        time.sleep(backoff)
                        backoff *= 2.0
                        continue
                    else:
                        # 429 Retry exhaustion: record failure on circuit breaker
                        self.circuit_breaker.record_failure()
                        break
                else:
                    self.circuit_breaker.record_failure()
                    break

        self.telemetry["errors"] += 1
        logger.error("All Groq API attempts failed for role %s. Triggering fallback. Error: %s", role, last_error)
        return self._fallback_generate(role, model, system_prompt, user_prompt, start_time, error=last_error)

    def _fallback_generate(
        self,
        role: str,
        target_model: str,
        system_prompt: str,
        user_prompt: str,
        start_time: float,
        error: Optional[str] = None
    ) -> Dict[str, Any]:
        """Local offline generator fallback producing structured deterministic output for testing/air-gap."""
        duration = round(time.time() - start_time, 3)
        fallback_content = self._synthesize_offline_blueprint(role, user_prompt)
        return {
            "role": role,
            "model": f"{target_model} (offline_fallback)",
            "content": fallback_content,
            "latency_seconds": duration,
            "prompt_tokens": len(user_prompt.split()),
            "completion_tokens": len(fallback_content.split()),
            "source": "offline_fallback",
            "error": error,
            "status": "fallback_success"
        }

    def _synthesize_offline_blueprint(self, role: str, prompt: str) -> str:
        """Generate structured deterministic blueprint section based on role."""
        domain_summary = _sanitize_prompt_for_summary(prompt)
        if role == "pm_agent":
            return (
                f"# Product Requirements Document (PRD)\n\n"
                f"## 1. Executive Summary\n"
                f"Autonomous engineering workflow synthesized for {domain_summary}.\n\n"
                f"## 2. Target Personas\n"
                f"- Principal Architects & Tech Leads\n- Full-Stack Engineers\n\n"
                f"## 3. Key Requirements\n"
                f"- [P0] Sub-second voice ingestion & diarization\n"
                f"- [P0] Multi-model council deliberation for {domain_summary}\n"
                f"- [P1] Automated Git Pull Request creation\n\n"
                f"## 4. Threat Model (STRIDE)\n"
                f"- Zero API key leakage; strict local storage in BYOK vault.\n"
                f"- Prompt injection & delimiter breakout resistance verified."
            )
        elif role == "architect_agent":
            return (
                f"# System Architecture & Database Specification\n\n"
                f"```mermaid\n"
                f"flowchart TD\n"
                f"    Client[\"Client Surface (Web/Desktop)\"] --> API[\"FastAPI Gateway\"]\n"
                f"    API --> Council[\"Multi-Model Council\"]\n"
                f"    Council --> DB[(\"PostgreSQL / Local Store\")]\n"
                f"```\n\n"
                f"## Database DDL for {domain_summary}\n"
                f"```sql\n"
                f"CREATE TABLE IF NOT EXISTS projects (\n"
                f"    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),\n"
                f"    title VARCHAR(255) NOT NULL,\n"
                f"    created_at TIMESTAMPTZ DEFAULT NOW()\n"
                f");\n"
                f"```"
            )
        elif role == "ui_agent":
            return (
                f"# UI/UX Design System Specification\n\n"
                f"## Design Tokens\n"
                f"- Background: `#010308` (Obsidian deep)\n"
                f"- Accent: `#38bdf8` (Sapphire cyan)\n"
                f"- Borders: Hairline 1px `#1e293b`\n\n"
                f"## Component Hierarchy for {domain_summary}\n"
                f"- `StudioLayout` -> `MonolithCanvas` + `AmbientVoiceDock`"
            )
        elif role == "systems_agent":
            return (
                f"# Systems Lifecycle & Sequence Flow\n\n"
                f"```mermaid\n"
                f"sequenceDiagram\n"
                f"    autonumber\n"
                f"    actor User\n"
                f"    participant UI as Monolith Studio\n"
                f"    participant API as FastAPI Gateway\n"
                f"    participant Council as Multi-Model Council\n\n"
                f"    User->>UI: Spoken Brainstorm (Audio Stream)\n"
                f"    UI->>API: 16kHz PCM Chunks via WebSocket\n"
                f"    API->>Council: BM25 Context + Transcribed Query\n"
                f"    Council-->>UI: Real-Time Blueprint Telemetry\n"
                f"```"
            )
        elif role == "agile_agent":
            return (
                f"# Agile Delivery Plan & Task Checklist\n\n"
                f"## Milestone 1: Core Foundation for {domain_summary}\n"
                f"- [ ] `[NEW] src/model_router.py`: Verified multi-model dispatch\n"
                f"- [ ] `[NEW] src/council_engine.py`: DAG execution\n\n"
                f"## Milestone 2: WebSocket Streaming\n"
                f"- [ ] `[NEW] src/api/server.py`: FastAPI live bridge"
            )
        else:
            return (
                f"# Master Execution Bundle Synthesis\n\n"
                f"Consolidated technical blueprint for downstream execution agents ({domain_summary}).\n"
                f"Target verification: `python -m unittest discover tests`"
            )

    def get_telemetry(self) -> Dict[str, Any]:
        """Return cumulative telemetry and usage statistics."""
        return dict(self.telemetry)
