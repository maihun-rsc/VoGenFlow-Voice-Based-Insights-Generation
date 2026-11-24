"""
Patch web_app/index.html and frontend_demo.html with:
1. Re-architected 2-Column Decramped Council Modal with Pinned Action Bar
2. Diagram Zoom In, Zoom Out, Reset, Fullscreen, Mouse Wheel Zoom & Drag-to-Pan
3. Clean UI Badges for [NEW] (CREATE FILE), [MODIFY], and [DELETE]
4. Plain English System Architecture & Microservice Map references
5. Clean .split(placeholder).join(replacement) to prevent $' corruption
"""

import re
from pathlib import Path

NEW_COUNCIL_MODAL = """  <!-- ========================================================================= -->
  <!-- MODAL: CALLABLE COUNCIL CHAMBER (2-COLUMN DECRAMPED ARCHITECTURE)           -->
  <!-- ========================================================================= -->
  <div id="councilModalOverlay" class="fixed inset-0 bg-black/90 backdrop-blur-md z-50 flex items-center justify-center p-3 sm:p-5 md:p-6 overflow-y-auto hidden">
    <div class="w-full max-w-5xl max-h-[92vh] flex flex-col rounded-3xl monolith-bezel border shadow-[0_0_100px_rgba(0,0,0,0.98)] overflow-hidden my-auto" style="border-color: var(--bezel-border); background: var(--bezel-bg);">
      
      <!-- Pinned Header (Always Visible) -->
      <div class="flex items-center justify-between border-b px-5 py-3.5 gap-2 shrink-0" style="border-color: var(--card-border); background: var(--card-bg);">
        <div class="flex items-center space-x-2.5">
          <span class="w-2.5 h-2.5 rounded-full bg-amber-400 animate-pulse"></span>
          <div>
            <span class="text-xs font-mono-telemetry tracking-widest uppercase font-bold" style="color: var(--text-main);">COUNCIL CHAMBER // MULTI-AGENT PROTOCOL</span>
            <span class="text-[10px] font-mono-telemetry block text-neutral-400" style="color: var(--text-muted);">Specialized Autonomous Deliberation &amp; Verification DAG</span>
          </div>
        </div>
        <div class="flex items-center space-x-2.5 shrink-0">
          <button onclick="triggerGenerate()" class="hidden sm:inline-flex px-3.5 py-1.5 rounded-xl font-bold text-xs font-mono-telemetry transition-all shadow-md items-center space-x-1.5 hover:opacity-90 active:scale-95" style="background: var(--accent-gold); color: #000;" title="Convene Multi-Agent Council Now">
            <span>CONVENE</span>
            <span class="text-sm">&#10022;</span>
          </button>
          <button onclick="toggleCouncilModal()" class="px-2.5 py-1.5 rounded-xl border text-xs font-mono-telemetry hover:text-white transition-colors" style="border-color: var(--card-border); color: var(--text-muted);" title="Close [ESC]">
            [ESC]
          </button>
        </div>
      </div>

      <!-- 2-Column Body: Left Orbit Stage (7 cols) + Right Thoughts Dossier (5 cols) -->
      <div class="flex-1 overflow-y-auto p-4 sm:p-5 grid grid-cols-1 lg:grid-cols-12 gap-5 items-stretch">
        
        <!-- Left Column: Deliberation Orbit Stage -->
        <div class="lg:col-span-7 flex flex-col justify-center items-center relative min-h-[360px] sm:min-h-[400px] rounded-2xl border overflow-hidden p-4 select-none" style="background: var(--input-bg); border-color: var(--card-border);">
          <!-- Ambient Orbit Lines & Glow (Responsive %-based) -->
          <div class="absolute w-[90%] max-w-[480px] h-[250px] rounded-[100%] border border-dashed pointer-events-none opacity-25" style="border-color: var(--accent-gold);"></div>
          <div class="absolute w-[70%] max-w-[350px] h-[175px] rounded-[100%] border pointer-events-none" style="border-color: var(--card-border);"></div>
          <div class="absolute w-64 h-64 rounded-full pointer-events-none opacity-15" style="background: radial-gradient(circle, var(--accent-gold) 0%, transparent 70%);"></div>

          <!-- Center Hub -->
          <div class="text-center z-10 px-3 max-w-xs pointer-events-none my-auto">
            <div class="text-[10px] font-mono-telemetry uppercase tracking-widest text-amber-400 font-bold">COUNCIL SEATS</div>
            <div class="text-lg sm:text-xl font-medium tracking-tight mt-1" style="color: var(--text-main);">Multi-Agent DAG</div>
            <div class="text-xs font-serif-luxury italic mt-0.5" style="color: var(--text-muted);">Specialized Autonomous Deliberation</div>
            <div class="mt-3 inline-flex items-center space-x-1.5 px-3 py-1 rounded-full text-[10px] font-mono-telemetry border" style="border-color: var(--card-border); background: var(--card-bg); color: var(--accent-gold);">
              <span class="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
              <span id="councilStatusText">STATUS: READY</span>
            </div>
          </div>

          <!-- Seat 1: Strategist (Top Center) -->
          <div 
            id="seat-station-strategist"
            onclick="selectSeat('Strategist', 'GPT-OSS-120B', 'Principal PM', 'Synthesizes strategic PRD, user personas, non-functional SLAs, and STRIDE security boundaries.', 'STAGE 1 // STRATEGY')" 
            class="seat-station absolute top-3 left-1/2 transform -translate-x-1/2 text-center cursor-pointer group transition-transform hover:scale-105 z-20"
          >
            <div class="w-10 h-10 sm:w-11 sm:h-11 rounded-2xl flex items-center justify-center mx-auto border-2 shadow-lg transition-colors group-hover:border-emerald-300 border-emerald-400/80" style="background: var(--card-bg);">
              <span class="text-[11px] font-mono-telemetry font-bold text-emerald-400">STR</span>
            </div>
            <div class="text-[10px] font-semibold mt-1" style="color: var(--text-main);">Strategist</div>
            <div class="text-[8px] font-mono-telemetry text-emerald-400 font-medium">Principal PM</div>
          </div>

          <!-- Seat 2: Architect (Right Top) -->
          <div 
            id="seat-station-architect"
            onclick="selectSeat('Architect', 'GPT-OSS-120B', 'Systems Core', 'Designs system architecture, microservice topology, and partitioned PostgreSQL 16 DDL with Row-Level Security.', 'STAGE 2 // FAN-OUT')" 
            class="seat-station absolute top-8 right-4 sm:right-8 text-center cursor-pointer group transition-transform hover:scale-105"
          >
            <div class="w-10 h-10 sm:w-11 sm:h-11 rounded-2xl flex items-center justify-center mx-auto border-2 shadow-lg transition-colors group-hover:border-amber-300 border-amber-400/80" style="background: var(--card-bg);">
              <span class="text-[11px] font-mono-telemetry font-bold text-amber-400">ARC</span>
            </div>
            <div class="text-[10px] font-semibold mt-1" style="color: var(--text-main);">Architect</div>
            <div class="text-[8px] font-mono-telemetry text-amber-400 font-medium">Systems Core</div>
          </div>

          <!-- Seat 3: Curator (Right Bottom) -->
          <div 
            id="seat-station-curator"
            onclick="selectSeat('Curator', 'GPT-OSS-120B', 'RAG Engine', 'Grounds specifications against 16 curated enterprise blueprints, BM25 indices, and design tokens.', 'STAGE 2 // FAN-OUT')" 
            class="seat-station absolute bottom-6 right-4 sm:right-8 text-center cursor-pointer group transition-transform hover:scale-105"
          >
            <div class="w-10 h-10 sm:w-11 sm:h-11 rounded-2xl flex items-center justify-center mx-auto border-2 shadow-lg transition-colors group-hover:border-amber-300 border-amber-400/80" style="background: var(--card-bg);">
              <span class="text-[11px] font-mono-telemetry font-bold text-amber-400">CUR</span>
            </div>
            <div class="text-[10px] font-semibold mt-1" style="color: var(--text-main);">Curator</div>
            <div class="text-[8px] font-mono-telemetry text-amber-400 font-medium">RAG Engine</div>
          </div>

          <!-- Seat 4: Linguist (Left Bottom) -->
          <div 
            id="seat-station-linguist"
            onclick="selectSeat('Linguist', 'WHISPER-LARGE-V3', 'Whisper STT', 'Captures ambient microphone stream, performs VAD segmentation, and transcribes voice intent.', 'STAGE 0 // CAPTURE')" 
            class="seat-station absolute bottom-6 left-4 sm:left-8 text-center cursor-pointer group transition-transform hover:scale-105"
          >
            <div class="w-10 h-10 sm:w-11 sm:h-11 rounded-2xl flex items-center justify-center mx-auto border-2 shadow-lg transition-colors group-hover:border-purple-300 border-purple-400/80" style="background: var(--card-bg);">
              <span class="text-[11px] font-mono-telemetry font-bold text-purple-400">LIN</span>
            </div>
            <div class="text-[10px] font-semibold mt-1" style="color: var(--text-main);">Linguist</div>
            <div class="text-[8px] font-mono-telemetry text-purple-400 font-medium">Whisper STT</div>
          </div>

          <!-- Seat 5: The Elder (Left Top) -->
          <div 
            id="seat-station-elder"
            onclick="selectSeat('The Elder', 'GPT-OSS-120B', 'Consensus Verifier', 'Compiles agile execution tasks, verifies consistency, and gates deliverable consensus.', 'DAG STAGE 3')" 
            class="seat-station absolute top-8 left-4 sm:left-8 text-center cursor-pointer group transition-transform hover:scale-105"
          >
            <div class="w-10 h-10 sm:w-11 sm:h-11 rounded-2xl flex items-center justify-center mx-auto border-2 shadow-lg transition-colors group-hover:border-cyan-300 border-cyan-400/80" style="background: var(--card-bg);">
              <span class="text-[11px] font-mono-telemetry font-bold text-cyan-400">ELD</span>
            </div>
            <div class="text-[10px] font-semibold mt-1" style="color: var(--text-main);">The Elder</div>
            <div class="text-[8px] font-mono-telemetry text-cyan-400 font-medium">Consensus Gate</div>
          </div>

        </div>

        <!-- Right Column: Dedicated Interactive Seat Inspector Dossier -->
        <div id="seatInspectorCard" class="lg:col-span-5 flex flex-col justify-between p-4 sm:p-5 rounded-2xl border transition-all space-y-4" style="background: var(--card-bg); border-color: var(--card-border);">
          <div class="space-y-3">
            <div class="flex items-center justify-between gap-2 border-b pb-3" style="border-color: var(--card-border);">
              <div class="flex items-center space-x-2">
                <span id="seatInspectorBadge" class="px-2.5 py-0.5 rounded-full text-[9px] font-mono-telemetry font-bold bg-emerald-500/15 text-emerald-400 border border-emerald-500/30">SEAT: STRATEGIST</span>
                <span id="seatInspectorStage" class="px-2.5 py-0.5 rounded-full text-[9px] font-mono-telemetry border border-emerald-500/30 text-emerald-400 bg-emerald-500/10 font-semibold">STAGE 1</span>
              </div>
              <button id="seatInspectorArtifactBtn" onclick="viewSeatArtifact('PRD.md')" class="px-2.5 py-1 rounded-xl text-[10px] font-mono-telemetry font-semibold border flex items-center space-x-1 transition-all hover:opacity-90" style="border-color: var(--accent-gold); color: var(--accent-gold); background: rgba(212,175,55,0.1);">
                <span>VIEW PRD</span>
                <span>&#10022;</span>
              </button>
            </div>

            <div>
              <div id="seatInspectorTitle" class="text-sm font-semibold tracking-wide" style="color: var(--text-main);">Strategist &mdash; Principal Technical PM</div>
              <div id="seatInspectorModel" class="text-[10px] font-mono-telemetry mt-0.5" style="color: var(--text-subtle);">// OPENAI/GPT-OSS-120B // GROQ LPU</div>
              <div id="seatInspectorDesc" class="text-xs font-light leading-relaxed mt-2" style="color: var(--text-muted);">Synthesizes strategic PRD, user personas, non-functional SLAs, and STRIDE security boundaries.</div>
            </div>

            <!-- Real-Time Agent Thinking & Deliberation Flow -->
            <div id="seatInspectorThoughtsBox" class="p-3 rounded-xl border text-xs font-mono-telemetry leading-relaxed flex items-start space-x-2 overflow-y-auto max-h-[190px]" style="background: var(--input-bg); border-color: var(--card-border);">
              <span class="text-amber-400 shrink-0 mt-0.5">&#128173;</span>
              <div class="w-full">
                <div class="text-[9px] uppercase tracking-wider font-bold text-amber-400">AGENT DELIBERATION RATIONALE &amp; THOUGHTS</div>
                <div id="seatInspectorThoughts" class="mt-1 text-neutral-300 italic" style="color: var(--text-main);">
                  Ready to deliberate. Convenes upon voice capture or prompt submission to synthesize target architecture.
                </div>
              </div>
            </div>
          </div>

          <div class="text-[10px] font-mono-telemetry italic pt-2 border-t" style="color: var(--text-subtle); border-color: var(--card-border);">
            Select any agent station on the left to inspect real-time thought chains and role deliverables.
          </div>
        </div>

      </div>

      <!-- Pinned Modal Footer (ALWAYS VISIBLE across 16:9, 16:10, and Mobile) -->
      <div class="flex items-center justify-between border-t px-5 py-3 gap-3 shrink-0" style="border-color: var(--card-border); background: var(--bezel-bg);">
        <span class="text-[10px] font-mono-telemetry hidden sm:inline" style="color: var(--text-muted);">Council DAG: Strategist &rarr; Architect || Curator || Linguist &rarr; The Elder</span>
        <div class="flex items-center space-x-3 w-full sm:w-auto justify-end">
          <button onclick="toggleCouncilModal()" class="px-4 py-2 rounded-xl border text-xs font-mono-telemetry transition-colors hover:border-amber-400" style="background: var(--input-bg); border-color: var(--card-border); color: var(--text-main);">
            CLOSE
          </button>
          <button id="modalConveneBtn" onclick="triggerGenerate()" class="px-6 py-2.5 rounded-xl font-bold text-xs font-mono-telemetry transition-all shadow-xl flex items-center space-x-2 hover:opacity-90 transform active:scale-95" style="background: var(--accent-gold); color: #000;">
            <span>CONVENE COUNCIL &amp; GENERATE</span>
            <span class="text-sm">&#10022;</span>
          </button>
        </div>
      </div>

    </div>
  </div>"""

def patch_file(file_path: Path):
    text = file_path.read_text(encoding="utf-8")

    # 1. Replace Council Modal if it contains old one
    if '<div id="councilModalOverlay"' in text:
        modal_start = text.find('<!-- MODAL: CALLABLE COUNCIL CHAMBER')
        if modal_start != -1:
            modal_end = text.find('<!-- ========================================================================= -->\n  <!-- JAVASCRIPT APPLICATION LOGIC', modal_start)
            if modal_end != -1:
                text = text[:modal_start] + NEW_COUNCIL_MODAL + "\n\n  " + text[modal_end:]
                print(f"[OK] Replaced Council Modal in {file_path.name}")

    # 2. Add Mermaid Interactive Zoom & Pan CSS if missing
    zoom_css = """
    /* Interactive Mermaid Diagram Zoom & Pan Styling */
    .mermaid-viewer { position: relative; }
    .mermaid-viewport { overflow: hidden; position: relative; touch-action: none; cursor: grab; }
    .mermaid-viewport:active { cursor: grabbing; }
    .mermaid-content { transform-origin: center center; transition: transform 0.05s ease-out; }
    .mermaid svg { max-width: 100% !important; height: auto !important; min-width: 500px; }
"""
    if "/* Interactive Mermaid Diagram Zoom & Pan Styling */" not in text:
        text = text.replace("</style>", zoom_css + "\n  </style>")
        print(f"[OK] Injected Mermaid Zoom CSS into {file_path.name}")

    # 3. Add Mermaid Zoom & Pan JavaScript helper functions
    zoom_js = """
    // -------------------------------------------------------------------------
    // Interactive Mermaid Diagram Pan & Zoom Engine
    // -------------------------------------------------------------------------
    const mermaidStates = {};

    function initMermaidState(id) {
      if (!mermaidStates[id]) {
        mermaidStates[id] = { scale: 1.0, x: 0, y: 0, isDragging: false, startX: 0, startY: 0 };
      }
    }

    function updateMermaidTransform(id) {
      const state = mermaidStates[id];
      const content = document.getElementById(`mermaid-content-${id}`);
      const label = document.getElementById(`mermaid-zoom-label-${id}`);
      if (content) {
        content.style.transform = `translate(${state.x}px, ${state.y}px) scale(${state.scale})`;
      }
      if (label) {
        label.innerText = `ZOOM: ${Math.round(state.scale * 100)}%`;
      }
    }

    function zoomMermaid(id, factor) {
      initMermaidState(id);
      const state = mermaidStates[id];
      state.scale = Math.min(Math.max(state.scale * factor, 0.4), 4.0);
      updateMermaidTransform(id);
    }

    function resetMermaid(id) {
      initMermaidState(id);
      mermaidStates[id] = { scale: 1.0, x: 0, y: 0, isDragging: false, startX: 0, startY: 0 };
      updateMermaidTransform(id);
    }

    function handleMermaidWheel(e, id) {
      e.preventDefault();
      initMermaidState(id);
      const factor = e.deltaY < 0 ? 1.15 : 0.85;
      zoomMermaid(id, factor);
    }

    function toggleFullscreenMermaid(id) {
      const card = document.getElementById(`mermaid-card-${id}`);
      if (!card) return;
      if (!card.classList.contains('fixed')) {
        card.classList.add('fixed', 'inset-4', 'z-50', 'flex', 'flex-col', 'max-h-[calc(100vh-2rem)]');
        card.classList.remove('my-6');
        const vp = document.getElementById(`mermaid-viewport-${id}`);
        if (vp) vp.classList.add('flex-1', 'h-full');
      } else {
        card.classList.remove('fixed', 'inset-4', 'z-50', 'flex', 'flex-col', 'max-h-[calc(100vh-2rem)]');
        card.classList.add('my-6');
        const vp = document.getElementById(`mermaid-viewport-${id}`);
        if (vp) vp.classList.remove('flex-1', 'h-full');
        resetMermaid(id);
      }
    }

    // Attach Pan drag listeners
    document.addEventListener('mousedown', (e) => {
      const vp = e.target.closest('.mermaid-viewport');
      if (!vp) return;
      const id = vp.id.replace('mermaid-viewport-', '');
      initMermaidState(id);
      const state = mermaidStates[id];
      state.isDragging = true;
      state.startX = e.clientX - state.x;
      state.startY = e.clientY - state.y;
    });

    document.addEventListener('mousemove', (e) => {
      for (const id in mermaidStates) {
        const state = mermaidStates[id];
        if (state.isDragging) {
          state.x = e.clientX - state.startX;
          state.y = e.clientY - state.startY;
          updateMermaidTransform(id);
        }
      }
    });

    document.addEventListener('mouseup', () => {
      for (const id in mermaidStates) {
        const state = mermaidStates[id];
        if (state.isDragging) {
          state.isDragging = false;
        }
      }
    });
"""
    if "// Interactive Mermaid Diagram Pan & Zoom Engine" not in text:
        text = text.replace("let isCouncilOpen = false;", zoom_js + "\n    let isCouncilOpen = false;")
        print(f"[OK] Injected Mermaid Zoom JS into {file_path.name}")

    # 4. Overhaul formatMarkdown for Zoomable Mermaid and Badge Parsing
    old_start = text.find("function formatMarkdown(text) {")
    old_end = text.find("// =========================================================================\n    // 7. Interactive RAG Architecture Chat Client")
    
    if old_start != -1 and old_end != -1:
        new_format_md = """function formatMarkdown(text) {
      if (!text) return '';
      
      // 1. Extract code blocks into tokens FIRST so inner code/arrows are never mangled
      const codeBlocks = [];
      let processed = text.replace(/```([a-zA-Z0-9_\\-\\.]*)\\n([\\s\\S]*?)```/g, (match, lang, code) => {
        const id = `___VOGEN_CODE_BLOCK_${codeBlocks.length}___`;
        codeBlocks.push({ lang: (lang || '').toLowerCase().trim(), code: code.trim() });
        return id;
      });

      // 2. Parse Markdown Tables (| Col 1 | Col 2 |) into styled HTML tables
      processed = processed.replace(/((?:\\|[^\\n]+\\|\\r?\\n?){2,})/g, (tableMatch) => {
        const lines = tableMatch.trim().split('\\n').filter(l => l.trim().startsWith('|'));
        if (lines.length < 2) return tableMatch;
        
        let tableHtml = '<div class="my-5 overflow-x-auto rounded-xl border" style="border-color: var(--card-border); background: var(--card-bg);"><table class="w-full text-left border-collapse text-xs font-mono-telemetry">';
        let isHeader = true;
        
        for (let i = 0; i < lines.length; i++) {
          const line = lines[i].trim();
          if (/^\\|[\\s\\-:\\|]+\\|$/.test(line)) {
            isHeader = false;
            continue;
          }
          const cells = line.split('|').slice(1, -1).map(c => c.trim());
          if (isHeader) {
            tableHtml += '<thead style="background: var(--bezel-bg); border-bottom: 1px solid var(--card-border);"><tr>';
            cells.forEach(cell => {
              tableHtml += `<th class="p-3 font-semibold uppercase tracking-wider text-[11px]" style="color: var(--accent-gold); border-bottom: 1px solid var(--card-border);">${cell}</th>`;
            });
            tableHtml += '</tr></thead><tbody>';
            isHeader = false;
          } else {
            tableHtml += '<tr class="border-b transition-colors hover:bg-neutral-800/20" style="border-color: var(--card-border);">';
            cells.forEach(cell => {
              tableHtml += `<td class="p-3 leading-relaxed" style="color: var(--text-main);">${cell}</td>`;
            });
            tableHtml += '</tr>';
          }
        }
        tableHtml += '</tbody></table></div>';
        return tableHtml;
      });

      // 3. Clean diff badges: replace raw [NEW], [MODIFY], [DELETE] with UI telemetry tags
      processed = processed.replace(/`?\\[NEW\\]`?/gi, '<span class="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-mono-telemetry font-bold border border-emerald-500/40 bg-emerald-500/10 text-emerald-400">CREATE FILE</span>');
      processed = processed.replace(/`?\\[MODIFY\\]`?/gi, '<span class="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-mono-telemetry font-bold border border-amber-500/40 bg-amber-500/10 text-amber-400">MODIFY</span>');
      processed = processed.replace(/`?\\[DELETE\\]`?/gi, '<span class="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-mono-telemetry font-bold border border-rose-500/40 bg-rose-500/10 text-rose-400">DELETE</span>');

      // 4. Headers, Bold, Italics, Checkboxes, Lists
      processed = processed.replace(/^### (.*$)/gim, '<h3 class="text-base font-semibold mt-6 mb-2 tracking-wide" style="color: var(--text-main);">$1</h3>');
      processed = processed.replace(/^## (.*$)/gim, '<h2 class="text-lg font-semibold mt-8 mb-3 tracking-wide pb-2 border-b" style="color: var(--text-main); border-color: var(--card-border);">$1</h2>');
      processed = processed.replace(/^# (.*$)/gim, '<h1 class="text-2xl md:text-3xl font-light mt-8 mb-4 tracking-tight font-serif-luxury italic pb-3 border-b" style="color: var(--accent-gold); border-color: var(--card-border);">$1</h1>');
      processed = processed.replace(/\\*\\*(.*?)\\*\\*/g, '<strong class="font-semibold" style="color: var(--text-main);">$1</strong>');
      processed = processed.replace(/\\*(.*?)\\*/g, '<em class="italic" style="color: var(--text-muted);">$1</em>');
      processed = processed.replace(/- \\[x\\] (.*$)/gim, '<div class="flex items-center space-x-2.5 py-1 text-xs font-mono-telemetry" style="color: var(--text-main);"><span class="text-amber-400 font-bold">&#9745;</span> <span>$1</span></div>');
      processed = processed.replace(/- \\[ \\] (.*$)/gim, '<div class="flex items-center space-x-2.5 py-1 text-xs font-mono-telemetry" style="color: var(--text-muted);"><span class="opacity-60 font-bold">&#9744;</span> <span>$1</span></div>');
      processed = processed.replace(/^\\s*[-*]\\s+(.*$)/gim, '<li class="ml-5 list-disc text-xs md:text-sm py-1 leading-relaxed" style="color: var(--text-muted);">$1</li>');
      processed = processed.replace(/\\n\\n+/g, '</p><p class="text-xs md:text-sm leading-relaxed my-3" style="color: var(--text-muted);">');

      // 5. Safely re-inject Code Blocks using .split().join() to eliminate $' placeholder mangling
      codeBlocks.forEach((block, idx) => {
        const placeholder = `___VOGEN_CODE_BLOCK_${idx}___`;
        let replacement = '';
        const encodedCode = encodeURIComponent(block.code);
        
        if (block.lang === 'mermaid') {
          // Normalize Unicode non-breaking characters & auto-quote unquoted bracket labels
          const safeMermaid = block.code
            .replace(/\\u2011/g, '-')
            .replace(/\\u202f/g, ' ')
            .replace(/\\[([^"\\]\\n]+)\\]/g, (m, inner) => {
              const trimmed = inner.trim();
              if ((trimmed.startsWith('"') && trimmed.endsWith('"')) || (trimmed.startsWith("'") && trimmed.endsWith("'"))) {
                return `[${trimmed}]`;
              }
              return `["${trimmed.replace(/"/g, "'")}"]`;
            });

          replacement = `<div class="mermaid-viewer my-6 rounded-xl border overflow-hidden shadow-lg" id="mermaid-card-${idx}" style="border-color: var(--card-border); background: var(--code-bg);">
            <div class="px-4 py-2 border-b flex flex-wrap items-center justify-between gap-2 text-[10px] font-mono-telemetry" style="border-color: var(--card-border); background: var(--bezel-bg); color: var(--text-muted);">
              <span class="uppercase font-bold tracking-wider flex items-center gap-1.5" style="color: var(--accent-gold);">
                <span>&#10022;</span> ARCHITECTURAL DIAGRAM
              </span>
              <div class="flex items-center space-x-1.5">
                <button onclick="zoomMermaid('${idx}', 1.25)" class="px-2 py-0.5 rounded border border-neutral-700 bg-neutral-800/60 hover:bg-neutral-700 text-white font-mono-telemetry" title="Zoom In">[+] ZOOM</button>
                <button onclick="zoomMermaid('${idx}', 0.8)" class="px-2 py-0.5 rounded border border-neutral-700 bg-neutral-800/60 hover:bg-neutral-700 text-white font-mono-telemetry" title="Zoom Out">[-] ZOOM</button>
                <button onclick="resetMermaid('${idx}')" class="px-2 py-0.5 rounded border border-neutral-700 bg-neutral-800/60 hover:bg-neutral-700 text-white font-mono-telemetry" title="Reset Zoom">RESET</button>
                <button onclick="toggleFullscreenMermaid('${idx}')" class="px-2 py-0.5 rounded border border-neutral-700 bg-neutral-800/60 hover:bg-neutral-700 text-white font-mono-telemetry" title="Fullscreen Diagram">&#9974; FULLSCREEN</button>
                <button onclick="navigator.clipboard.writeText(decodeURIComponent('${encodedCode}')); showToast('Mermaid syntax copied');" class="px-2 py-0.5 rounded border border-neutral-700 bg-neutral-800/60 hover:bg-neutral-700 text-amber-400 font-mono-telemetry" title="Copy Syntax">COPY</button>
              </div>
            </div>
            <div class="mermaid-viewport relative w-full overflow-hidden p-4 md:p-6 flex justify-center items-center min-h-[300px] select-none cursor-grab" id="mermaid-viewport-${idx}" onwheel="handleMermaidWheel(event, '${idx}')">
              <div class="mermaid-content transform origin-center transition-transform duration-75" id="mermaid-content-${idx}">
                <pre class="mermaid text-center" style="background: transparent;">${safeMermaid}</pre>
              </div>
            </div>
            <div class="px-4 py-1.5 border-t text-[9px] font-mono-telemetry flex justify-between items-center" style="border-color: var(--card-border); background: var(--bezel-bg); color: var(--text-subtle);">
              <span>Use mouse wheel to zoom &middot; Click &amp; drag to pan diagram</span>
              <span id="mermaid-zoom-label-${idx}">ZOOM: 100%</span>
            </div>
          </div>`;
        } else {
          const safeCode = block.code
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;');
          replacement = `<div class="my-5 rounded-xl border overflow-hidden" style="border-color: var(--card-border); background: var(--code-bg);">
            <div class="px-4 py-2 border-b flex items-center justify-between text-[10px] font-mono-telemetry" style="border-color: var(--card-border); background: var(--bezel-bg); color: var(--text-muted);">
              <span class="uppercase font-semibold tracking-wider" style="color: var(--accent-gold);">${block.lang || 'CODE'}</span>
              <button onclick="navigator.clipboard.writeText(decodeURIComponent('${encodedCode}')); showToast('Code copied to clipboard');" class="hover:opacity-100 transition-opacity font-bold">COPY</button>
            </div>
            <pre class="p-4 md:p-5 overflow-x-auto text-xs font-mono-telemetry leading-relaxed" style="color: var(--code-text);"><code>${safeCode}</code></pre>
          </div>`;
        }
        processed = processed.split(placeholder).join(replacement);
      });

      return `<div class="space-y-4 font-light">${processed}</div>`;
    }

    """
        text = text[:old_start] + new_format_md + text[old_end:]
        print(f"[OK] Replaced formatMarkdown in {file_path.name}")
    else:
        print(f"[WARN] Could not find formatMarkdown boundaries in {file_path.name}")

    # 5. Clean up any leftover 'C4 TOPOLOGY' in sample blueprint
    text = text.replace('// C4 TOPOLOGY', '// SYSTEM ARCHITECTURE')
    text = text.replace('1. C4 Container Topology', '1. System Architecture & Microservice Map')

    file_path.write_text(text, encoding="utf-8")
    print(f"[OK] Successfully patched and saved {file_path.name}")

if __name__ == "__main__":
    patch_file(Path("web_app/index.html"))
    patch_file(Path("frontend_demo.html"))
