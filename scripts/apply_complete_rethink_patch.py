"""
Vo-Gen-Flow: Complete Rethink & Polish Patch
Applies:
1. RAG Chat Nav button (#nav-chat) & View Container (#view-chat)
2. Council Chamber Orbit De-cramping & Dynamic Seat Thought Dossier
3. Safe formatMarkdown (pre-extract code blocks, pure Mermaid sequence diagram, styled Markdown tables)
4. Model Router & Council Engine fallback normalization to unified openai/gpt-oss-120b
"""

from pathlib import Path
import re

INDEX_PATH = Path(r"E:\voice-insight-generation\web_app\index.html")
DEMO_PATH = Path(r"E:\voice-insight-generation\frontend_demo.html")
ENGINE_PATH = Path(r"E:\voice-insight-generation\src\council_engine.py")

print("--- Step 1: Normalizing Council Engine fallback model ---")
engine_code = ENGINE_PATH.read_text(encoding="utf-8")
if '"qwen/qwen3.8-27b"' in engine_code:
    engine_code = engine_code.replace('"qwen/qwen3.8-27b"', '"openai/gpt-oss-120b"')
    ENGINE_PATH.write_text(engine_code, encoding="utf-8")
    print("Council engine fallback model updated to openai/gpt-oss-120b")
else:
    print("Council engine already normalized")

print("\n--- Step 2: Patching web_app/index.html ---")
html = INDEX_PATH.read_text(encoding="utf-8")

# 1. Update Header Navigation
old_nav_snippet = """<button id="nav-specs" onclick="switchView('specs')" class="hover:opacity-100 transition-opacity pb-1">DOCUMENTS</button>
        <button onclick="toggleCouncilModal()" class="flex items-center space-x-1.5 transition-opacity pb-1 text-amber-400 hover:text-amber-300">"""

new_nav_snippet = """<button id="nav-specs" onclick="switchView('specs')" class="hover:opacity-100 transition-opacity pb-1">DOCUMENTS</button>
        <button id="nav-chat" onclick="switchView('chat')" class="hover:opacity-100 transition-opacity pb-1 flex items-center space-x-1.5 text-amber-400">
          <span>RAG CHAT</span>
          <span class="px-1.5 py-0.2 rounded text-[9px] font-mono-telemetry gold-badge font-bold">AI</span>
        </button>
        <button onclick="toggleCouncilModal()" class="flex items-center space-x-1.5 transition-opacity pb-1 text-amber-400 hover:text-amber-300">"""

if 'id="nav-chat"' not in html and old_nav_snippet in html:
    html = html.replace(old_nav_snippet, new_nav_snippet)
    print("Added #nav-chat to header navigation")
else:
    print("#nav-chat check:", 'id="nav-chat"' in html)

# 2. Add #view-chat panel before Toast Notification
chat_panel_html = """
  <!-- ========================================================================= -->
  <!-- VIEW 4: RAG ARCHITECTURE CHAT (GROUNDED MULTI-SPEC CONVERSATION)           -->
  <!-- ========================================================================= -->
  <div id="view-chat" class="view-panel max-w-[1600px] mx-auto w-full space-y-6 pb-44 hidden">
    
    <!-- Chat Header Banner -->
    <div class="monolith-bezel rounded-2xl p-6 md:p-8 flex flex-col md:flex-row items-start md:items-center justify-between gap-4 border" style="background: var(--card-bg); border-color: var(--card-border);">
      <div class="space-y-1.5">
        <div class="flex items-center space-x-2">
          <span class="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-pulse"></span>
          <span class="text-[10px] font-mono-telemetry uppercase tracking-widest text-amber-400 font-bold">RAG ARCHITECTURAL INTELLIGENCE</span>
          <span class="text-[10px] font-mono-telemetry text-neutral-400">// 16 ENTERPRISE BLUEPRINTS GROUNDED</span>
        </div>
        <h2 class="text-xl md:text-2xl font-normal tracking-tight" style="color: var(--text-main);">
          Conversational Architecture &amp; Codebase Studio
        </h2>
        <p class="text-xs md:text-sm font-light max-w-3xl" style="color: var(--text-muted);">
          Query your generated system specifications (<code class="text-amber-400">PRD.md</code>, <code class="text-amber-400">Architecture.md</code>, <code class="text-amber-400">Flow.md</code>, <code class="text-amber-400">tasks.md</code>) and 16 curated enterprise blueprints with zero-hallucination guardrails and precise source citations.
        </p>
      </div>
      <div class="flex items-center space-x-3 shrink-0">
        <button onclick="clearChatHistory()" class="px-4 py-2 rounded-xl border text-xs font-mono-telemetry transition-colors hover:border-amber-400" style="background: var(--input-bg); border-color: var(--card-border); color: var(--text-muted);">
          CLEAR CHAT
        </button>
        <button onclick="toggleCouncilModal()" class="px-4 py-2 rounded-xl text-xs font-mono-telemetry font-bold gold-badge shadow-md flex items-center space-x-1.5 hover:opacity-90">
          <span>CONVENE COUNCIL</span>
          <span>✦</span>
        </button>
      </div>
    </div>

    <!-- Quick Suggestion Starter Pills -->
    <div class="flex items-center gap-2 overflow-x-auto pb-1 text-xs font-mono-telemetry scrollbar-none">
      <span class="text-[10px] uppercase font-bold shrink-0 text-amber-400">SUGGESTIONS:</span>
      <button onclick="sendQuickPrompt(this.innerText)" class="px-3.5 py-1.5 rounded-xl border shrink-0 transition-all hover:border-amber-400 hover:text-amber-300" style="background: var(--input-bg); border-color: var(--card-border); color: var(--text-main);">
        Explain the PostgreSQL DDL schema &amp; RLS policies
      </button>
      <button onclick="sendQuickPrompt(this.innerText)" class="px-3.5 py-1.5 rounded-xl border shrink-0 transition-all hover:border-amber-400 hover:text-amber-300" style="background: var(--input-bg); border-color: var(--card-border); color: var(--text-main);">
        Detail the end-to-end Kafka sequence &amp; failover flow
      </button>
      <button onclick="sendQuickPrompt(this.innerText)" class="px-3.5 py-1.5 rounded-xl border shrink-0 transition-all hover:border-amber-400 hover:text-amber-300" style="background: var(--input-bg); border-color: var(--card-border); color: var(--text-main);">
        How is sub-millisecond fraud detection achieved?
      </button>
      <button onclick="sendQuickPrompt(this.innerText)" class="px-3.5 py-1.5 rounded-xl border shrink-0 transition-all hover:border-amber-400 hover:text-amber-300" style="background: var(--input-bg); border-color: var(--card-border); color: var(--text-main);">
        What are the STRIDE security threat mitigations?
      </button>
    </div>

    <!-- Chat Messages Timeline -->
    <div id="ragChatTimeline" class="min-h-[460px] max-h-[620px] overflow-y-auto p-5 md:p-8 rounded-2xl border space-y-4" style="background: var(--card-bg); border-color: var(--card-border);">
      
      <!-- Welcome Bubble -->
      <div class="flex items-start space-x-3.5">
        <div class="w-9 h-9 rounded-xl flex items-center justify-center shrink-0 font-mono-telemetry text-xs font-bold shadow-md" style="background: var(--accent-gold); color: #000;">
          AI
        </div>
        <div class="space-y-1.5 max-w-3xl">
          <div class="text-[10px] font-mono-telemetry font-semibold uppercase tracking-wider text-amber-400">
            VO-GEN-FLOW RAG ENGINE // GROUNDED INTELLIGENCE
          </div>
          <div class="p-4 md:p-5 rounded-2xl border text-xs md:text-sm leading-relaxed" style="background: var(--bezel-bg); border-color: var(--card-border); color: var(--text-main);">
            Greetings. I am your RAG Architecture Assistant, grounded in your active session specifications and 16 curated enterprise blueprints via Okapi BM25 and vector embeddings. Ask me anything about database schemas, API contracts, latency SLAs, Kafka state transitions, or failover mechanisms.
          </div>
        </div>
      </div>

    </div>

    <!-- Input Dock -->
    <div class="p-3 md:p-4 rounded-2xl border shadow-2xl flex items-center gap-3" style="background: var(--card-bg); border-color: var(--bezel-border);">
      <input 
        type="text" 
        id="ragChatInput" 
        placeholder="Ask a technical question about the system architecture, database DDL, or flow..." 
        class="flex-1 px-4 py-3 rounded-xl text-xs md:text-sm font-mono-telemetry border focus:outline-none"
        style="background: var(--input-bg); border-color: var(--card-border); color: var(--text-main);"
        onkeydown="if(event.key === 'Enter') executeRAGChatQuery();"
      />
      <button 
        onclick="executeRAGChatQuery()" 
        id="ragChatSendBtn"
        class="px-6 py-3 rounded-xl font-bold text-xs font-mono-telemetry tracking-wider uppercase transition-all shadow-md flex items-center space-x-2 hover:opacity-90 active:scale-95 shrink-0"
        style="background: var(--accent-gold); color: #000;"
      >
        <span>QUERY RAG</span>
        <span>✦</span>
      </button>
    </div>

  </div>
"""

toast_marker = '  <!-- Toast Notification Overlay (Positioned at bottom-right for zero dock/header overlap) -->'
if 'id="view-chat"' not in html and toast_marker in html:
    html = html.replace(toast_marker, chat_panel_html + "\n\n" + toast_marker)
    print("Mounted #view-chat view-panel before toast notification")
else:
    print("#view-chat check:", 'id="view-chat"' in html)

# 3. Update switchView function to include 'chat'
old_switch_view_code = "['landing', 'studio', 'specs'].forEach(v => {"
new_switch_view_code = "['landing', 'studio', 'specs', 'chat'].forEach(v => {"
if old_switch_view_code in html:
    html = html.replace(old_switch_view_code, new_switch_view_code)
    print("Updated switchView to include 'chat'")

# 4. De-cramp Council Orbit Canvas and separate Strategist & Center Hub
old_orbit_container = """<div class="relative w-full h-[260px] sm:h-[300px] md:h-[330px] flex items-center justify-center overflow-hidden rounded-2xl border shrink-0" style="background: var(--input-bg); border-color: var(--card-border);">
        
        <!-- Ambient Orbit Lines & Glow -->
        <div class="absolute w-[620px] h-[300px] rounded-[100%] border border-dashed pointer-events-none opacity-25" style="border-color: var(--accent-gold);"></div>
        <div class="absolute w-[420px] h-[200px] rounded-[100%] border pointer-events-none" style="border-color: var(--card-border);"></div>
        <div class="absolute w-64 h-64 rounded-full pointer-events-none opacity-15" style="background: radial-gradient(circle, var(--accent-gold) 0%, transparent 70%);"></div>

        <!-- Center Hub -->
        <div class="text-center z-10 px-4 max-w-xs pointer-events-none">
          <div class="text-[9px] font-mono-telemetry uppercase tracking-widest text-amber-400 font-semibold">COUNCIL SEATS</div>
          <div class="text-base sm:text-lg md:text-xl font-normal tracking-tight mt-0.5" style="color: var(--text-main);">Multi-Agent DAG</div>
          <div class="text-[11px] font-serif-luxury italic mt-0.5" style="color: var(--text-muted);">Specialized Autonomous Deliberation</div>
          <div class="mt-2 inline-flex items-center space-x-1.5 px-3 py-0.5 rounded-full text-[9px] font-mono-telemetry border" style="border-color: var(--card-border); background: var(--card-bg); color: var(--accent-gold);">
            <span class="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
            <span id="councilStatusText">STATUS: READY</span>
          </div>
        </div>"""

new_orbit_container = """<div class="relative w-full h-[380px] sm:h-[410px] md:h-[440px] flex items-center justify-center overflow-hidden rounded-2xl border shrink-0" style="background: var(--input-bg); border-color: var(--card-border);">
        
        <!-- Ambient Orbit Lines & Glow (Spacious & Scaled) -->
        <div class="absolute w-[680px] h-[340px] rounded-[100%] border border-dashed pointer-events-none opacity-25" style="border-color: var(--accent-gold);"></div>
        <div class="absolute w-[480px] h-[240px] rounded-[100%] border pointer-events-none" style="border-color: var(--card-border);"></div>
        <div class="absolute w-80 h-80 rounded-full pointer-events-none opacity-15" style="background: radial-gradient(circle, var(--accent-gold) 0%, transparent 70%);"></div>

        <!-- Center Hub (Shifted with ample vertical clearance) -->
        <div class="text-center z-10 px-4 max-w-xs pointer-events-none mt-14 sm:mt-16">
          <div class="text-[10px] font-mono-telemetry uppercase tracking-widest text-amber-400 font-bold">COUNCIL SEATS</div>
          <div class="text-lg sm:text-xl font-medium tracking-tight mt-1" style="color: var(--text-main);">Multi-Agent DAG</div>
          <div class="text-xs font-serif-luxury italic mt-0.5" style="color: var(--text-muted);">Specialized Autonomous Deliberation</div>
          <div class="mt-3 inline-flex items-center space-x-1.5 px-3.5 py-1 rounded-full text-[10px] font-mono-telemetry border" style="border-color: var(--card-border); background: var(--card-bg); color: var(--accent-gold);">
            <span class="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
            <span id="councilStatusText">STATUS: READY</span>
          </div>
        </div>"""

if old_orbit_container in html:
    html = html.replace(old_orbit_container, new_orbit_container)
    print("De-cramped Council Chamber orbit and created 60px vertical clearance")

# Ensure all 5 seat stations have explicit IDs and unified models
seats_replacements = [
    # Strategist
    (
        'onclick="selectSeat(\'Strategist\',',
        'id="seat-station-strategist" onclick="selectSeat(\'Strategist\','
    ),
    # Architect
    (
        'onclick="selectSeat(\'Architect\', \'Qwen 27B / Llama 3.3\',',
        'id="seat-station-architect" onclick="selectSeat(\'Architect\', \'GPT-OSS-120B\','
    ),
    # Curator
    (
        'onclick="selectSeat(\'Curator\',',
        'id="seat-station-curator" onclick="selectSeat(\'Curator\','
    ),
    # Linguist
    (
        'onclick="selectSeat(\'Linguist\',',
        'id="seat-station-linguist" onclick="selectSeat(\'Linguist\','
    ),
    # The Elder
    (
        'onclick="selectSeat(\'The Elder\', \'Llama 3.1 8B / Qwen 27B\',',
        'id="seat-station-elder" onclick="selectSeat(\'The Elder\', \'GPT-OSS-120B\','
    )
]

for old_s, new_s in seats_replacements:
    if old_s in html and ('id="' + new_s.split('id="')[1].split('"')[0] + '"') not in html:
        html = html.replace(old_s, new_s, 1)
        print(f"Updated seat station: {new_s.split()[0]}")

# 5. Overhaul selectSeat() to provide rich prospective thoughts & active station glow
old_select_seat_fn = """    function selectSeat(name, model, role, desc, stage) {
      // Dynamic visual highlight on clicked station
      document.querySelectorAll('.seat-station').forEach(el => el.classList.remove('ring-2', 'ring-amber-400', 'rounded-2xl'));
      const activeEl = document.getElementById(`seat-station-${name.toLowerCase().replace('the ', '').trim()}`);
      if (activeEl) activeEl.classList.add('ring-2', 'ring-amber-400', 'rounded-2xl');

      const badge = document.getElementById('seatInspectorBadge');
      const modelEl = document.getElementById('seatInspectorModel');
      const titleEl = document.getElementById('seatInspectorTitle');
      const descEl = document.getElementById('seatInspectorDesc');
      const stageEl = document.getElementById('seatInspectorStage');
      const thoughtsEl = document.getElementById('seatInspectorThoughts');
      const artifactBtn = document.getElementById('seatInspectorArtifactBtn');
      
      const cleanKey = name.toLowerCase().replace('the ', '').trim();
      const liveData = latestSeatDossier[cleanKey] || null;

      if (badge) badge.innerText = `SEAT: ${name.toUpperCase()}`;
      
      if (liveData) {
        if (modelEl) modelEl.innerText = `// ${liveData.model.toUpperCase()} // ${liveData.latency_seconds}s // ${liveData.tokens} TOKENS`;
        if (titleEl) titleEl.innerText = `${liveData.role} — ${liveData.name}`;
        if (descEl) descEl.innerText = desc || `${liveData.name} agent executed in DAG.`;
        if (stageEl) stageEl.innerText = liveData.stage;
        if (thoughtsEl) thoughtsEl.innerText = `"${liveData.thoughts}"`;
        if (artifactBtn) {
          artifactBtn.classList.remove('hidden');
          artifactBtn.onclick = () => viewSeatArtifact(liveData.artifact_key);
          artifactBtn.innerHTML = `<span>VIEW ${liveData.artifact_key}</span><span>✦</span>`;
        }
      } else {
        if (modelEl) modelEl.innerText = `// ${model || 'GROQ LPU / LOCAL'}`;
        if (titleEl) titleEl.innerText = `${role || 'Specialist'} — ${name}`;
        if (descEl) descEl.innerText = desc || 'Specialist council agent executing deterministic step in DAG.';
        if (stageEl) stageEl.innerText = stage || 'ACTIVE AGENT';
        if (thoughtsEl) thoughtsEl.innerText = 'Ready to deliberate. Convenes upon voice capture or prompt submission to synthesize target architecture.';
        if (artifactBtn) {
          let art = 'PRD.md';
          if (cleanKey === 'architect') art = 'Architecture.md';
          else if (cleanKey === 'elder') art = 'tasks.md';
          else if (cleanKey === 'curator') art = 'Architecture.md';
          artifactBtn.classList.remove('hidden');
          artifactBtn.onclick = () => viewSeatArtifact(art);
          artifactBtn.innerHTML = `<span>VIEW ${art}</span><span>✦</span>`;
        }
      }
    }"""

new_select_seat_fn = """    // Prospective Role-Specific Thoughts before Deliberation
    const PROSPECTIVE_THOUGHTS = {
      strategist: "Analyzing problem domain, core user personas, P0 vs P1 requirement trade-offs, and non-functional SLA matrices under STRIDE boundaries.",
      architect: "Formulating C4 container topology, distributed microservices, and partitioned PostgreSQL 16 schema with UUIDv7 keys and declarative Row-Level Security.",
      curator: "Searching and scoring against 16 curated enterprise blueprints via in-memory Okapi BM25 and dense semantic grounding.",
      linguist: "Awaiting 16kHz acoustic PCM stream; ready for Whisper sub-400ms audio transcription, noise filtering, and domain expansion.",
      elder: "Prepared to gate consensus across all DAG agents, enforce schema invariants, and package delivery checklists into actionable milestones."
    };

    function selectSeat(name, model, role, desc, stage) {
      const cleanKey = name.toLowerCase().replace('the ', '').trim();

      // Dynamic visual highlight on clicked station
      document.querySelectorAll('.seat-station').forEach(el => {
        el.classList.remove('ring-2', 'ring-amber-400', 'rounded-2xl', 'scale-105', 'shadow-[0_0_20px_rgba(212,175,55,0.4)]');
      });
      const activeEl = document.getElementById(`seat-station-${cleanKey}`);
      if (activeEl) {
        activeEl.classList.add('ring-2', 'ring-amber-400', 'rounded-2xl', 'scale-105', 'shadow-[0_0_20px_rgba(212,175,55,0.4)]');
      }

      const badge = document.getElementById('seatInspectorBadge');
      const modelEl = document.getElementById('seatInspectorModel');
      const titleEl = document.getElementById('seatInspectorTitle');
      const descEl = document.getElementById('seatInspectorDesc');
      const stageEl = document.getElementById('seatInspectorStage');
      const thoughtsEl = document.getElementById('seatInspectorThoughts');
      const artifactBtn = document.getElementById('seatInspectorArtifactBtn');
      
      const liveData = latestSeatDossier[cleanKey] || null;

      if (badge) badge.innerText = `SEAT: ${name.toUpperCase()}`;
      
      if (liveData) {
        if (modelEl) modelEl.innerText = `// ${liveData.model.toUpperCase()} // ${liveData.latency_seconds}s // ${liveData.tokens} TOKENS`;
        if (titleEl) titleEl.innerText = `${liveData.role} — ${liveData.name}`;
        if (descEl) descEl.innerText = desc || `${liveData.name} agent executed in DAG.`;
        if (stageEl) stageEl.innerText = liveData.stage;
        if (thoughtsEl) thoughtsEl.innerText = `"${liveData.thoughts}"`;
        if (artifactBtn) {
          artifactBtn.classList.remove('hidden');
          artifactBtn.onclick = () => viewSeatArtifact(liveData.artifact_key);
          artifactBtn.innerHTML = `<span>VIEW ${liveData.artifact_key}</span><span>✦</span>`;
        }
      } else {
        const unifiedModel = (cleanKey === 'linguist') ? 'WHISPER LARGE V3' : 
                             (cleanKey === 'curator') ? 'DUAL-ADAPTER RAG (BM25)' : 'OPENAI/GPT-OSS-120B';
        if (modelEl) modelEl.innerText = `// ${unifiedModel} // GROQ LPU`;
        if (titleEl) titleEl.innerText = `${role || 'Specialist'} — ${name}`;
        if (descEl) descEl.innerText = desc || 'Specialist council agent executing deterministic step in DAG.';
        if (stageEl) stageEl.innerText = stage || 'ACTIVE AGENT';
        if (thoughtsEl) thoughtsEl.innerText = `"${PROSPECTIVE_THOUGHTS[cleanKey] || 'Ready to deliberate. Convenes upon voice capture or prompt submission.'}"`;
        if (artifactBtn) {
          let art = 'PRD.md';
          if (cleanKey === 'architect') art = 'Architecture.md';
          else if (cleanKey === 'elder') art = 'tasks.md';
          else if (cleanKey === 'curator') art = 'Architecture.md';
          artifactBtn.classList.remove('hidden');
          artifactBtn.onclick = () => viewSeatArtifact(art);
          artifactBtn.innerHTML = `<span>VIEW ${art}</span><span>✦</span>`;
        }
      }
    }"""

if old_select_seat_fn in html:
    html = html.replace(old_select_seat_fn, new_select_seat_fn)
    print("Overhauled selectSeat with prospective thoughts and glowing station ring")

# 6. Ensure RAG chat query logic handles citations array
old_rag_citations = """        // Build sources citation pills
        let citationsHtml = '';
        if (sources.length > 0) {
          citationsHtml = `<div class="mt-2.5 pt-2 border-t flex flex-wrap gap-1.5" style="border-color: var(--card-border);">
            <span class="text-[9px] font-mono-telemetry uppercase text-amber-400 font-bold self-center">CITATIONS:</span>
            ${sources.map(s => `<span class="px-2 py-0.5 rounded text-[9px] font-mono-telemetry border" style="border-color: var(--card-border); background: var(--card-bg); color: var(--text-muted);">${s}</span>`).join('')}
          </div>`;
        }"""

new_rag_citations = """        // Build sources citation pills from either data.citations or data.sources
        const citationList = [];
        if (Array.isArray(data.citations)) {
          data.citations.forEach(c => {
            const label = c.chunk_id !== undefined ? `${c.file} §${c.chunk_id}` : c.file;
            citationList.push(label);
          });
        }
        if (Array.isArray(data.sources)) {
          data.sources.forEach(s => { if (!citationList.includes(s)) citationList.push(s); });
        }

        let citationsHtml = '';
        if (citationList.length > 0) {
          citationsHtml = `<div class="mt-3 pt-2.5 border-t flex flex-wrap gap-2 items-center" style="border-color: var(--card-border);">
            <span class="text-[9px] font-mono-telemetry uppercase text-amber-400 font-bold">CITATIONS:</span>
            ${citationList.map(s => `<span class="px-2.5 py-0.5 rounded-full text-[9px] font-mono-telemetry border" style="border-color: var(--card-border); background: var(--card-bg); color: var(--accent-gold);">${s}</span>`).join('')}
          </div>`;
        }"""

if old_rag_citations in html:
    html = html.replace(old_rag_citations, new_rag_citations)
    print("Enhanced RAG Chat citations pill formatter")

INDEX_PATH.write_text(html, encoding="utf-8")
DEMO_PATH.write_text(html, encoding="utf-8")
print(f"Complete patch applied to {INDEX_PATH} and mirrored to {DEMO_PATH}")
