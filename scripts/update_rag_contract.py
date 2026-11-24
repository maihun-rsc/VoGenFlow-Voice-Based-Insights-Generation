from pathlib import Path

p = Path("src/rag_engine.py")
lines = p.read_text(encoding="utf-8").splitlines(keepends=True)

# Replace lines 924 to 962 with the compliant contract
new_lines = [
    '                context_block = f"[{Path(top_c.source_path).name} - Chunk {top_c.chunk_id}]:\\n" + clean_text\n',
    '\n',
    '        if not is_grounded:\n',
    '            answer = (\n',
    '                "Guardrail Notice: No sufficiently grounded context found in indexed documents "\n',
    '                f"matching query \'{clean_query}\'. Refusing to hallucinate unverified specifications."\n',
    '            )\n',
    '        elif active_router and hasattr(active_router, "generate"):\n',
    '            system_prompt = (\n',
    '                "You are the Vo-Gen-Flow Document Intelligence Engine. "\n',
    '                "Answer the user\'s question accurately using the retrieved technical documentation snippets below. "\n',
    '                "Cite your sources precisely using [Filename - ChunkID]. "\n',
    '                "Provide code snippets or architectural explanations where helpful."\n',
    '            )\n',
    '            user_prompt = f"Retrieved Context:\\n{context_block}\\n\\nUser Question:\\n{clean_query}"\n',
    '            res = active_router.generate("default", system_prompt, user_prompt)\n',
    '            answer = res.get("content", "")\n',
    '        else:\n',
    '            # Extractive deterministic answer for air-gapped / offline mode\n',
    '            top_chunk, top_score = grounded_matches[0]\n',
    '            clean_top, _ = sanitize_document_content(top_chunk.content)\n',
    '            answer = (\n',
    '                f"Grounded insight from {Path(top_chunk.source_path).name} (Section {top_chunk.chunk_id}, score {top_score:.2f}):\\n\\n"\n',
    '                f"{clean_top[:600]}\\n\\n"\n',
    '                f"*Source: [{Path(top_chunk.source_path).name} - Chunk {top_chunk.chunk_id}]*"\n',
    '            )\n',
]

result = lines[:924] + new_lines + lines[953:]
p.write_text("".join(result), encoding="utf-8")
print("[OK] Updated rag_engine.py with test-compliant contract")
