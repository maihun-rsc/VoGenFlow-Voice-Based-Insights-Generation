from pathlib import Path

p = Path("src/rag_engine.py")
lines = p.read_text(encoding="utf-8").splitlines(keepends=True)

# Find where '            "answer": answer,' starts
idx = -1
for i, l in enumerate(lines):
    if '"answer": answer,' in l:
        idx = i
        break

if idx != -1:
    lines.insert(idx, '        return {\n            "query": clean_query,\n')
    p.write_text("".join(lines), encoding="utf-8")
    print(f"[OK] Inserted return statement at index {idx}")
else:
    print("[ERROR] Could not find answer line")
