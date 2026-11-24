from pathlib import Path

file_path = Path("E:/voice-insight-generation/src/model_router.py")
content = file_path.read_text(encoding="utf-8")

start_marker = "    def _synthesize_offline_blueprint(self, role: str, prompt: str) -> str:"
end_marker = "    def get_telemetry(self) -> Dict[str, Any]:"

assert start_marker in content, "start marker not found"
assert end_marker in content, "end marker not found"

new_blueprint = '''    def _synthesize_offline_blueprint(self, role: str, prompt: str) -> str:
        """Generate structured deterministic blueprint stub for offline test execution."""
        domain_summary = _sanitize_prompt_for_summary(prompt) or "System Specification"

        stubs = {
            "pm_agent": (
                f"# Project Requirements Document (PRD): {domain_summary}\\n\\n"
                f"### Problem Statement\\nOffline specification stub for {domain_summary}.\\n\\n"
                f"### Functional Requirements\\n- **[P0] Core Ingestion:** Validated input processing.\\n\\n"
                f"### Non-Functional SLAs\\n- P99 Latency: < 50ms"
            ),
            "architect_agent": (
                f"# System Architecture & Data Models: {domain_summary}\\n\\n"
                f"### Architecture Overview\\nOffline component map for {domain_summary}.\\n\\n"
                f"```mermaid\\nflowchart TD\\n    A[Client] --> B[API Gateway]\\n```\\n\\n"
                f"```sql\\n-- Schema for {domain_summary}\\nCREATE TABLE IF NOT EXISTS system_records (\\n"
                f"    id UUID PRIMARY KEY,\\n    created_at TIMESTAMPTZ DEFAULT NOW()\\n);\\n```"
            ),
            "ui_agent": (
                f"# Design Tokens & UI Architecture: {domain_summary}\\n\\n"
                f"### Design Tokens\\n- Primary: #0A0A0A\\n- Surface: #121212"
            ),
            "systems_agent": (
                f"# Systems Lifecycle & Flow: {domain_summary}\\n\\n"
                f"```mermaid\\nsequenceDiagram\\n    Client->>Gateway: Request\\n```\\n\\n"
                f"### Failure Recovery Matrix\\n| Failure | Detection | Recovery |\\n|---|---|---|\\n| Node Crash | Heartbeat | Restart |"
            ),
            "agile_agent": (
                f"# Agile Delivery Plan & Task Checklist: {domain_summary}\\n\\n"
                f"## Milestone 1: Core Foundation for {domain_summary}\\n- [ ] [NEW] src/main.py\\n\\n"
                f"## Verification Plan\\n`pytest tests/`"
            ),
            "diff_agent": (
                f"# Master Execution Bundle Synthesis\\n\\n"
                f"Consolidated technical blueprint for downstream execution agents ({domain_summary}).\\n"
                f"Target verification: `pytest tests/`"
            )
        }
        return stubs.get(role, f"# Specification Section for {role}: {domain_summary}\\n\\nOffline stub for {domain_summary}.")

'''

pre = content[:content.index(start_marker)]
post = content[content.index(end_marker):]
new_content = pre + new_blueprint + post

file_path.write_text(new_content, encoding="utf-8")
print("Successfully replaced _synthesize_offline_blueprint")
