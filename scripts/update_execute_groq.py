from pathlib import Path
import re

file_path = Path("E:/voice-insight-generation/src/model_router.py")
content = file_path.read_text(encoding="utf-8")

start_marker = "    def _execute_groq_call("
end_marker = "    def _call_lm_studio("

assert start_marker in content, "start marker not found"
assert end_marker in content, "end marker not found"

new_execute_groq = '''    def _execute_groq_call(
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

'''

pre = content[:content.index(start_marker)]
post = content[content.index(end_marker):]
new_content = pre + new_execute_groq + post

file_path.write_text(new_content, encoding="utf-8")
print("Successfully updated _execute_groq_call with failover cascade and 429 wait-and-retry")
