import re
from pathlib import Path

p = Path("src/rag_engine.py")
text = p.read_text(encoding="utf-8")

# Replace broken multi-line f-strings
text = re.sub(
    r'context_block = f"\[Path\(top_c\.source_path\)\.name\}[^"]*?\n\{clean_text\}"',
    'context_block = f"[{Path(top_c.source_path).name} · Chunk {top_c.chunk_id}]:\\n" + clean_text',
    text
)

text = re.sub(
    r'user_prompt = f"Retrieved Context:\s*\n\{context_block\}\s*\n\s*\nUser Question:\s*\n\{clean_query\}"',
    'user_prompt = f"Retrieved Context:\\n{context_block}\\n\\nUser Question:\\n{clean_query}"',
    text
)

text = re.sub(
    r'answer = \(\s*f"### Grounded Insight: \{Path\(top_chunk\.source_path\)\.name\} \(Score: \{top_score:\.2f\}\)\s*\n\s*\n"\s*\n\s*f"\{clean_top\[:600\]\}\\n\\n"\s*\n\s*f"\*Source: \[.*?\]\*"',
    'answer = (\n                f"### Grounded Insight: {Path(top_chunk.source_path).name} (Score: {top_score:.2f})\\n\\n"\n                f"{clean_top[:600]}\\n\\n"\n                f"*Source: [{Path(top_chunk.source_path).name} · Chunk {top_chunk.chunk_id}]*"',
    text
)

p.write_text(text, encoding="utf-8")
print("[OK] rag_engine.py syntax repaired")
