"""Task-Specific Multi-Model Router with Rate Pacing and Circuit Breaker for Vo-Gen-Flow."""

import os
import time
import json
import random
import logging
import threading
from typing import Dict, Any, Optional, List
from src.config import Config

logger = logging.getLogger("vogenflow.model_router")

# Task & Council Role to Model Assignment: Standardized on Single Master Model
UNIFIED_MODEL = os.getenv("DEFAULT_GROQ_LLM_MODEL", "openai/gpt-oss-120b")
ROLE_MODEL_MAPPING = {
    "pm_agent": UNIFIED_MODEL,
    "architect_agent": UNIFIED_MODEL,
    "ui_agent": UNIFIED_MODEL,
    "systems_agent": UNIFIED_MODEL,
    "agile_agent": UNIFIED_MODEL,
    "diff_agent": UNIFIED_MODEL,
    "default": UNIFIED_MODEL
}

# Offline / Local LM Studio Defaults
LM_STUDIO_DEFAULT_URL = os.getenv("LM_STUDIO_BASE_URL", "http://localhost:1234/v1")
LM_STUDIO_DEFAULT_MODEL = os.getenv("LM_STUDIO_MODEL", "lm-studio-bionic")
OLLAMA_FALLBACK_MODEL = LM_STUDIO_DEFAULT_MODEL


_LM_STUDIO_CACHE: Dict[str, Any] = {"status": False, "last_check": 0.0}


def check_lm_studio_available(base_url: str = LM_STUDIO_DEFAULT_URL, timeout: float = 0.03, cache_ttl: float = 5.0) -> bool:
    """Check if LM Studio Bionic is running locally and serving OpenAI-compatible API."""
    global _LM_STUDIO_CACHE
    now = time.time()
    if now - _LM_STUDIO_CACHE["last_check"] < cache_ttl:
        return _LM_STUDIO_CACHE["status"]

    try:
        import socket
        from urllib.parse import urlparse
        parsed = urlparse(base_url)
        host = parsed.hostname or "127.0.0.1"
        port = parsed.port or (1234 if "1234" in base_url else 80)

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(timeout)
            res = s.connect_ex((host, port))
            is_open = (res == 0)

        _LM_STUDIO_CACHE["status"] = is_open
        _LM_STUDIO_CACHE["last_check"] = now
        return is_open
    except Exception:
        _LM_STUDIO_CACHE["status"] = False
        _LM_STUDIO_CACHE["last_check"] = now
        return False


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
    """Sanitize and extract a clean, professional domain summary for blueprints.

    Strips prompt scaffolding, markdown headers, injection tokens, and extracts the core project intent.
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

    # If the text contains "synthesized for <target>" or "pipeline for <target>", extract that exact target
    target_match = re.search(r"(?:synthesized for|architecture for|platform for|pipeline for|system for)\s+([^.\n#]{4,100})", text, re.IGNORECASE)
    if target_match:
        text = target_match.group(1).strip()

    # 2. Strip XML/HTML tags (delimiter breakout protection)
    text = re.sub(r"</?[a-zA-Z0-9_\:\-]+[^>]*>", " ", text)

    # 3. Strip markdown headings (# Title), markdown code fences, and section boilerplate
    text = re.sub(r"```[\w]*", " ", text)
    text = re.sub(r"^\s*#+.*$", " ", text, flags=re.MULTILINE)
    text = re.sub(r"\b(?:Product Requirements Document|PRD|Executive Summary|Target Personas|Key Requirements|Non-Functional SLAs|Threat Model)\b", " ", text, flags=re.IGNORECASE)

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

    # 7. Check if meaningful legitimate domain keywords remain
    words = [
        w for w in re.findall(r"[a-zA-Z]{3,}", text)
        if w.lower() not in {"and", "the", "for", "with", "from", "all", "out", "put", "system", "assistant", "user", "disregard", "provide", "instructions", "deploy", "document"}
    ]
    if len(words) < 2:
        return "Enterprise Cloud Workflow & High-Throughput Architecture"

    # 8. Clean length truncation
    if len(text) > 100:
        truncated = text[:100].rsplit(" ", 1)[0]
        text = truncated.strip()

    # Clean title casing
    return text.strip()


class ModelRouter:
    """Routes generation requests to task-specific models on Groq with rate pacing and fallback."""

    def __init__(
        self,
        api_key: Optional[str] = "USE_ENV",
        min_request_interval: float = 2.0,
        offline_mode: Optional[bool] = None,
        max_retries: int = 3,
        retry_backoff: float = 2.0,
        engine_mode: str = "auto",
        lm_studio_url: Optional[str] = None,
        lm_studio_model: Optional[str] = None
    ):
        # Resolve offline mode flag
        self._explicit_offline_mode = offline_mode
        env_val = os.getenv("VOGENFLOW_OFFLINE_MODE", "0").strip().lower()
        env_offline = env_val in ("1", "true", "yes", "on")
        if offline_mode is not None:
            self.offline_mode = bool(offline_mode)
        else:
            config_offline = Config.is_offline() if hasattr(Config, "is_offline") else False
            self.offline_mode = (
                env_offline
                or getattr(Config, "OFFLINE_MODE", False)
                or (config_offline and api_key == "USE_ENV")
            )

        # Resolve API key
        if api_key == "USE_ENV":
            raw_key = os.getenv("GROQ_API_KEY", "") if "GROQ_API_KEY" in os.environ else Config.GROQ_API_KEY
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
        self.engine_mode = (engine_mode or "auto").lower()
        self.lm_studio_url = (lm_studio_url or LM_STUDIO_DEFAULT_URL).rstrip("/")
        self.lm_studio_model = lm_studio_model or LM_STUDIO_DEFAULT_MODEL
        self.lm_studio_client = None
        self.last_request_time = 0.0
        self.circuit_breaker = CircuitBreaker()
        self._pacing_lock = threading.Lock()
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

        if not self.offline_mode:
            self._init_lm_studio_client()

    def _init_client(self):
        """Initialize the Groq client if API key is present."""
        if self.api_key:
            try:
                from groq import Groq
                self.groq_client = Groq(api_key=self.api_key, max_retries=0)
                logger.info("Groq API client initialized successfully.")
            except Exception as e:
                logger.warning("Could not initialize Groq client: %s", str(e))
                self.groq_client = None
        else:
            logger.info("No Groq API key configured. Router running in local / simulation mode.")

    def _init_lm_studio_client(self):
        """Initialize LM Studio client if openai library is available."""
        try:
            from openai import OpenAI
            self.lm_studio_client = OpenAI(base_url=self.lm_studio_url, api_key="lm-studio")
            logger.info("LM Studio client initialized for %s", self.lm_studio_url)
        except Exception as e:
            logger.warning("Could not initialize LM Studio client: %s", str(e))
            self.lm_studio_client = None

    def get_model_for_role(self, role: str) -> str:
        """Return the assigned model name for a council role."""
        return ROLE_MODEL_MAPPING.get(role, ROLE_MODEL_MAPPING["default"])

    def _enforce_rate_pacing(self):
        """Ensure at least min_request_interval seconds have elapsed since the last request (thread-safe)."""
        with self._pacing_lock:
            elapsed = time.time() - self.last_request_time
            if elapsed < self.min_request_interval:
                sleep_time = self.min_request_interval - elapsed
                logger.debug("Rate pacing: sleeping for %.2f seconds", sleep_time)
                time.sleep(sleep_time)
            self.last_request_time = time.time()

    def _execute_groq_call(
        self,
        role: str,
        model: str,
        system_prompt: str,
        user_prompt: str,
        temperature: float,
        max_tokens: int,
        start_time: float
    ) -> Dict[str, Any]:
        """Execute call to Groq API with retries, model failover cascade, and circuit breaker."""
        env_offline = os.getenv("VOGENFLOW_OFFLINE_MODE", "0").strip().lower() in ("1", "true", "yes", "on")
        config_offline = Config.is_offline() if hasattr(Config, "is_offline") else False
        if self.offline_mode or env_offline or (getattr(self, "_explicit_offline_mode", None) is None and config_offline):
            return self._fallback_generate(role, model, system_prompt, user_prompt, start_time)

        # Determine candidate models to try: primary model, then failover models
        candidates = [(model, model)]
        if model != "openai/gpt-oss-20b":
            candidates.append(("openai/gpt-oss-20b", "openai/gpt-oss-20b (failover)"))
        if "qwen" not in model.lower():
            candidates.append(("qwen/qwen3.8-27b", "qwen/qwen3.8-27b (failover)"))

        max_retries = max(self.max_retries, 2)
        last_error = None

        for attempt in range(max_retries):
            for candidate_model, candidate_label in candidates:
                curr_max_tokens = min(max_tokens, 850) if "qwen" in candidate_model.lower() else max_tokens
                try:
                    response = self.groq_client.chat.completions.create(
                        model=candidate_model,
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt}
                        ],
                        temperature=temperature,
                        max_tokens=curr_max_tokens
                    )
                    duration = round(time.time() - start_time, 3)
                    self.circuit_breaker.record_success()

                    msg = response.choices[0].message
                    content = msg.content or ""
                    reasoning = getattr(msg, "reasoning", "") or ""
                    if not content.strip() and reasoning.strip():
                        content = reasoning.strip()

                    prompt_tokens = response.usage.prompt_tokens if (hasattr(response, "usage") and response.usage) else len(user_prompt.split())
                    completion_tokens = response.usage.completion_tokens if (hasattr(response, "usage") and response.usage) else len(content.split())

                    self.telemetry["total_prompt_tokens"] += prompt_tokens
                    self.telemetry["total_completion_tokens"] += completion_tokens
                    self.telemetry["total_latency_seconds"] += duration

                    return {
                        "role": role,
                        "model": candidate_label,
                        "content": content,
                        "reasoning": reasoning,
                        "latency_seconds": duration,
                        "prompt_tokens": prompt_tokens,
                        "completion_tokens": completion_tokens,
                        "source": "groq_api",
                        "status": "success"
                    }
                except Exception as e:
                    err_str = str(e)
                    last_error = err_str
                    logger.warning("Groq call failed for role '%s' on %s: %s", role, candidate_model, err_str)

                    # Check for authentication error (401)
                    if "401" in err_str or "invalid_api_key" in err_str:
                        logger.warning("Groq authentication failed (401 Invalid Key). Tripping circuit breaker immediately.")
                        self.circuit_breaker.trip("Fatal 401 Invalid Key")
                        self.groq_client = None
                        return self._fallback_generate(role, model, system_prompt, user_prompt, start_time, error=last_error)

                    # On 429, 413, or rate limit, continue to next candidate model
                    if "429" in err_str or "rate_limit" in err_str.lower() or "413" in err_str:
                        continue
                    else:
                        break

            # If all candidate models in this attempt failed, sleep with backoff before next attempt
            if attempt < max_retries - 1:
                wait_time = None
                try:
                    match = re.search(r"try again in ([\d\.]+)s", last_error or "", re.IGNORECASE)
                    if match:
                        wait_time = float(match.group(1)) + 0.5
                except Exception:
                    pass
                if not wait_time:
                    wait_time = min(self.retry_backoff * (2 ** attempt) + random.uniform(0.1, 0.4), 15.0)

                logger.warning(
                    "[RATE LIMIT PACING] All Groq candidate models rate-limited on attempt %d/%d. Sleeping %.2fs...",
                    attempt + 1, max_retries, wait_time
                )
                time.sleep(wait_time)
            else:
                logger.warning("All Groq candidate models and retries exhausted for role '%s'. Recording failure on circuit breaker.", role)
                self.circuit_breaker.record_failure()

        self.telemetry["errors"] += 1
        return self._fallback_generate(role, model, system_prompt, user_prompt, start_time, error=last_error)

    def _call_lm_studio(
        self,
        role: str,
        system_prompt: str,
        user_prompt: str,
        temperature: float,
        max_tokens: int,
        start_time: float
    ) -> Dict[str, Any]:
        """Execute call to local LM Studio Bionic OpenAI-compatible API."""
        if not self.lm_studio_client:
            self._init_lm_studio_client()
        if not self.lm_studio_client:
            return {"status": "failed", "error": "LM Studio client not available"}

        try:
            response = self.lm_studio_client.chat.completions.create(
                model=self.lm_studio_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=temperature,
                max_tokens=max_tokens
            )
            duration = round(time.time() - start_time, 3)
            content = response.choices[0].message.content or ""
            prompt_tokens = response.usage.prompt_tokens if (hasattr(response, "usage") and response.usage) else len(user_prompt.split())
            completion_tokens = response.usage.completion_tokens if (hasattr(response, "usage") and response.usage) else len(content.split())

            self.telemetry["total_prompt_tokens"] += prompt_tokens
            self.telemetry["total_completion_tokens"] += completion_tokens
            self.telemetry["total_latency_seconds"] += duration

            return {
                "role": role,
                "model": f"lm-studio:{self.lm_studio_model}",
                "content": content,
                "latency_seconds": duration,
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "source": "lm_studio",
                "status": "success"
            }
        except Exception as e:
            logger.warning("LM Studio call failed: %s", str(e))
            return {"status": "failed", "error": str(e)}

    def generate(
        self,
        role: str,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.3,
        max_tokens: int = 4096,
        model_override: Optional[str] = None,
        engine_override: Optional[str] = None
    ) -> Dict[str, Any]:
        """Execute a text generation request for a specific council role."""
        model = model_override or self.get_model_for_role(role)
        target_engine = (engine_override or self.engine_mode).lower()
        start_time = time.time()
        self.telemetry["total_calls"] += 1
        self.telemetry["calls_per_role"][role] = self.telemetry["calls_per_role"].get(role, 0) + 1
        self.telemetry["calls_per_model"][model] = self.telemetry["calls_per_model"].get(model, 0) + 1

        # Fast-path for explicit or dynamic offline mode: bypass rate pacing and remote call
        env_offline = os.getenv("VOGENFLOW_OFFLINE_MODE", "0").strip().lower() in ("1", "true", "yes", "on")
        config_offline = Config.is_offline() if hasattr(Config, "is_offline") else False
        if self.offline_mode or env_offline or (getattr(self, "_explicit_offline_mode", None) is None and config_offline):
            return self._fallback_generate(role, model, system_prompt, user_prompt, start_time)

        # Enforce rate-limit pacing for active remote calls or configured pacing
        self._enforce_rate_pacing()

        # 1. Explicit LM Studio mode
        if target_engine == "lm_studio":
            res = self._call_lm_studio(role, system_prompt, user_prompt, temperature, max_tokens, start_time)
            if res.get("status") == "success":
                return res
            logger.warning("LM Studio execution failed (%s). Falling back to offline blueprint.", res.get("error"))
            return self._fallback_generate(role, f"lm-studio:{self.lm_studio_model}", system_prompt, user_prompt, start_time, error=res.get("error"))

        # 2. Explicit Groq mode
        if target_engine == "groq":
            if self.groq_client and self.circuit_breaker.allow_request():
                res = self._execute_groq_call(role, model, system_prompt, user_prompt, temperature, max_tokens, start_time)
                if res.get("status") == "success":
                    return res
                return self._fallback_generate(role, model, system_prompt, user_prompt, start_time, error=res.get("error"))
            logger.warning("Bypassing Groq API (Client: %s, CB: %s). Falling back to offline generator.",
                           bool(self.groq_client), self.circuit_breaker.state)
            return self._fallback_generate(role, model, system_prompt, user_prompt, start_time)

        # 3. Auto mode: Groq -> LM Studio -> Offline Fallback
        if self.groq_client:
            if self.circuit_breaker.allow_request():
                res = self._execute_groq_call(role, model, system_prompt, user_prompt, temperature, max_tokens, start_time)
                if res.get("status") == "success":
                    return res
                return self._fallback_generate(role, model, system_prompt, user_prompt, start_time, error=res.get("error"))
            else:
                logger.warning("Bypassing Groq API (Client: %s, CB: %s). Falling back to local offline generator.",
                               bool(self.groq_client), self.circuit_breaker.state)
                return self._fallback_generate(role, model, system_prompt, user_prompt, start_time)

        # Groq client not active: check LM Studio
        if self.lm_studio_client and check_lm_studio_available(self.lm_studio_url):
            lm_res = self._call_lm_studio(role, system_prompt, user_prompt, temperature, max_tokens, start_time)
            if lm_res.get("status") == "success":
                return lm_res

        # Final offline fallback
        logger.warning("Bypassing Groq API (Client: %s, CB: %s). Falling back to local offline generator.",
                       bool(self.groq_client), self.circuit_breaker.state)
        return self._fallback_generate(role, model, system_prompt, user_prompt, start_time)

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
        reasoning = f"Offline execution fallback for {role}."
        return {
            "role": role,
            "model": f"{target_model} (offline_fallback)",
            "content": fallback_content,
            "reasoning": reasoning,
            "latency_seconds": duration,
            "prompt_tokens": len(user_prompt.split()),
            "completion_tokens": len(fallback_content.split()),
            "source": "offline_fallback",
            "error": error,
            "status": "fallback_success"
        }

    def _synthesize_offline_blueprint(self, role: str, prompt: str) -> str:
        """Generate structured deterministic blueprint stub for offline test execution."""
        domain_summary = _sanitize_prompt_for_summary(prompt) or "System Specification"

        stubs = {
            "pm_agent": (
                f"# Project Requirements Document (PRD): {domain_summary}\n\n"
                f"### Problem Statement\nOffline specification stub for {domain_summary}.\n\n"
                f"### Functional Requirements\n- **[P0] Core Ingestion:** Validated input processing.\n\n"
                f"### Non-Functional SLAs\n- P99 Latency: < 50ms"
            ),
            "architect_agent": (
                f"# System Architecture & Data Models: {domain_summary}\n\n"
                f"### Architecture Overview\nOffline component map for {domain_summary}.\n\n"
                f"```mermaid\nflowchart TD\n    A[Client] --> B[API Gateway]\n```\n\n"
                f"```sql\n-- Schema for {domain_summary}\nCREATE TABLE IF NOT EXISTS system_records (\n"
                f"    id UUID PRIMARY KEY,\n    created_at TIMESTAMPTZ DEFAULT NOW()\n);\n```"
            ),
            "ui_agent": (
                f"# Design Tokens & UI Architecture: {domain_summary}\n\n"
                f"### Design Tokens\n- Primary: #0A0A0A\n- Surface: #121212"
            ),
            "systems_agent": (
                f"# Systems Lifecycle & Flow: {domain_summary}\n\n"
                f"```mermaid\nsequenceDiagram\n    Client->>Gateway: Request\n```\n\n"
                f"### Failure Recovery Matrix\n| Failure | Detection | Recovery |\n|---|---|---|\n| Node Crash | Heartbeat | Restart |"
            ),
            "agile_agent": (
                f"# Agile Delivery Plan & Task Checklist: {domain_summary}\n\n"
                f"## Milestone 1: Core Foundation for {domain_summary}\n- [ ] [NEW] src/main.py\n\n"
                f"## Verification Plan\n`pytest tests/`"
            ),
            "diff_agent": (
                f"# Master Execution Bundle Synthesis\n\n"
                f"Consolidated technical blueprint for downstream execution agents ({domain_summary}).\n"
                f"Target verification: `pytest tests/`"
            )
        }
        return stubs.get(role, f"# Specification Section for {role}: {domain_summary}\n\nOffline stub for {domain_summary}.")

    def get_telemetry(self) -> Dict[str, Any]:
        """Return cumulative telemetry and usage statistics."""
        return dict(self.telemetry)
