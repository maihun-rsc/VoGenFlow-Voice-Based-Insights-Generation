from pathlib import Path

p = Path("src/council_engine.py")
text = p.read_text(encoding="utf-8")

old_code = '''            arch_content = res.get("content", "")
            if not arch_content.strip():
                arch_content = self.router._synthesize_offline_blueprint("architect_agent", arch_prompt)
            with lock:
                artifacts["Architecture.md"] = arch_content'''

new_code = '''            arch_content = res.get("content", "")
            if not arch_content.strip():
                arch_content = self.router._synthesize_offline_blueprint("architect_agent", arch_prompt)
            elif "CREATE TABLE" not in arch_content:
                # Guarantee production PostgreSQL DDL is present even if model truncated
                arch_content += "\\n\\n" + self.router._synthesize_offline_blueprint("architect_agent", arch_prompt)
            with lock:
                artifacts["Architecture.md"] = arch_content'''

text = text.replace(old_code, new_code)

# Also ensure concise mermaid prompt
text = text.replace(
    '"1. System Architecture & Microservice Map: A clean Mermaid diagram (`flowchart TD`) representing the complete system topology',
    '"1. System Architecture & Microservice Map: A concise Mermaid diagram (`flowchart TD`, under 20 lines) representing the complete system topology'
)

p.write_text(text, encoding="utf-8")
print("[OK] Safeguarded Architecture.md DDL in src/council_engine.py")
