"""
Rethink Vo-Gen-Flow: Master Patch
1. Fix formatMarkdown: Extract code blocks before escaping, fix Mermaid sequence diagram syntax error, add markdown table parser.
2. Add RAG Architecture Chat feature: Header nav button, #view-chat UI canvas, interactive Q&A with /api/rag/query, suggestion pills.
3. Fix Council Chamber layout: De-cramp orbital ring, increase height to 380px, separate Strategist from center hub, add active seat ring highlight.
4. Dynamic Thought Dossier: Instantly updates rationale, thoughts, and artifacts when clicking any council seat.
Mirrors updates to frontend_demo.html.
"""

from pathlib import Path
import re

INDEX_PATH = Path(r"E:\voice-insight-generation\web_app\index.html")
DEMO_PATH = Path(r"E:\voice-insight-generation\frontend_demo.html")

content = INDEX_PATH.read_text(encoding="utf-8")

# =============================================================================
# 1. ADD RAG CHAT TO HEADER NAVIGATION
# =============================================================================
old_nav = """        <button id="nav-landing" onclick="switchView('landing')" class="hover:opacity-100 transition-opacity pb-1 font-medium" style="color: var(--text-main); border-b: 2px solid var(--accent-gold);">STUDIO</button>
        <button id="nav-specs" onclick="switchView('specs')" class="hover:opacity-100 transition-opacity pb-1">DOCUMENTS</button>
        <button onclick="toggleCouncilModal()" class="flex items-center space-x-1.5 transition-opacity pb-1 text-amber-400 hover:text-amber-300">"""

new_nav = """        <button id="nav-landing" onclick="switchView('landing')" class="hover:opacity-100 transition-opacity pb-1 font-medium" style="color: var(--text-main); border-b: 2px solid var(--accent-gold);">STUDIO</button>
        <button id="nav-specs" onclick="switchView('specs')" class="hover:opacity-100 transition-opacity pb-1">DOCUMENTS</button>
        <button id="nav-chat" onclick="switchView('chat')" class="hover:opacity-100 transition-opacity pb-1 flex items-center space-x-1.5" style="color: var(--text-muted);">
          <span>RAG CHAT</span>
          <span class="px-1.5 py-0.2 rounded text-[9px] font-mono-telemetry gold-badge font-bold">AI</span>
        </button>
        <button onclick="toggleCouncilModal()" class="flex items-center space-x-1.5 transition-opacity pb-1 text-amber-400 hover:text-amber-300">"""

if old_nav in content:
    content = content.replace(old_nav, new_nav)
    print("Added RAG CHAT button to header navigation")

# =============================================================================
# 2. ADD #view-chat CANVASES TO MAIN CONTAINER
# =============================================================================
chat_view_html = """
    <!-- ===================================================================== -->
    <!-- VIEW 3: RAG ARCHITECTURE CHAT (GROUNDED CONVERSATIONAL ASSISTANT)     -->
    <!-- ===================================================================== -->
    <div id="view-chat" class="hidden space-y-6 max-w-5xl mx-auto pb-24">
      <!-- Chat Header & Context Indicator -->
      <div class="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 p-4 rounded-2xl border" style="background: var(--card-bg); border-color: var(--card-border);">
        <div class="space-y-1">
          <div class="flex items-center space-x-2">
            <span class="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
            <span class="text-[10px] font-mono-telemetry uppercase tracking-widest text-amber-400 font-semibold">RAG ARCHITECTURAL INTELLIGENCE</span>
          </div>
          <h2 class="text-lg md:text-xl font-light" style="color: var(--text-main);">
            Conversational Codebase &amp; Spec Assistant
          </h2>
          <p class="text-xs font-light" style="color: var(--text-muted);">
            Grounded in active project specifications, C4 topologies, and 16 curated enterprise blueprints via Okapi BM25.
          </p>
        </div>
        <div class="flex items-center space-x-2">
          <button onclick="clearChatHistory()" class="px-3 py-1.5 rounded-lg border text-xs font-mono-telemetry hover:border-amber-400 transition-colors" style="border-color: var(--card-border); color: var(--text-muted);">
            CLEAR CHAT
          </button>
          <button onclick="switchView('specs')" class="px-3.5 py-1.5 rounded-lg text-xs font-mono-telemetry font-bold gold-badge shadow-sm">
            VIEW SPECS ✦
          </button>
        </div>
      </div>

      <!-- Quick Suggestion Starter Pills -->
      <div class="flex items-center gap-2 overflow-x-auto pb-1 text-xs font-mono-telemetry">
        <span class="text-[10px] uppercase font-bold shrink-0" style="color: var(--accent-gold);">PROMPTS:</span>
        <button onclick="sendQuickPrompt(this.innerText)" class="px-3 py-1.5 rounded-xl border shrink-0 transition-all hover:border-amber-400" style="background: var(--input-bg); border-color: var(--card-border); color: var(--text-main);">
          Explain the PostgreSQL DDL schema &amp; RLS policies
        </button>
        <button onclick="sendQuickPrompt(this.innerText)" class="px-3 py-1.5 rounded-xl border shrink-0 transition-all hover:border-amber-400" style="background: var(--input-bg); border-color: var(--card-border); color: var(--text-main);">
          How is sub-millisecond fraud detection achieved?
        </button>
        <button onclick="sendQuickPrompt(this.innerText)" class="px-3 py-1.5 rounded-xl border shrink-0 transition-all hover:border-amber-400" style="background: var(--input-bg); border-color: var(--card-border); color: var(--text-main);">
          Detail the end-to-end Kafka sequence &amp; failover flow
        </button>
        <button onclick="sendQuickPrompt(this.innerText)" class="px-3 py-1.5 rounded-xl border shrink-0 transition-all hover:border-amber-400" style="background: var(--input-bg); border-color: var(--card-border); color: var(--text-main);">
          What are the STRIDE security threat mitigations?
        </button>
      </div>

      <!-- Chat Timeline Messages Container -->
      <div id="ragChatTimeline" class="min-h-[420px] max-h-[560px] overflow-y-auto p-4 md:p-6 rounded-2xl border space-y-4" style="background: var(--card-bg); border-color: var(--card-border);">
        <!-- Welcome Message from Assistant -->
        <div class="flex items-start space-x-3">
          <div class="w-8 h-8 rounded-xl flex items-center justify-center shrink-0 font-mono-telemetry text-xs font-bold shadow-sm" style="background: var(--accent-gold); color: #000;">
            AI
          </div>
          <div class="space-y-1.5 max-w-3xl">
            <div class="text-[10px] font-mono-telemetry font-semibold uppercase tracking-wider" style="color: var(--accent-gold);">
              VO-GEN-FLOW RAG ENGINE // GROUNDED AGENT
            </div>
            <div class="p-4 rounded-2xl border text-xs md:text-sm leading-relaxed" style="background: var(--bezel-bg); border-color: var(--card-border); color: var(--text-main);">
              Hello! I am your RAG Architecture Assistant. I am grounded in your synthesized specifications (`PRD.md`, `architecture.md`, `flow.md`, `tasks.md`, `design_proposal.md`) and 16 curated production blueprints. Ask me any question about database schemas, API contracts, latency SLAs, or failover mechanisms.
            </div>
          </div>
        </div>
      </div>

      <!-- Chat Input Console -->
      <div class="p-3 md:p-4 rounded-2xl border shadow-xl flex items-center gap-3" style="background: var(--card-bg); border-color: var(--bezel-border);">
        <input 
          type="text" 
          id="ragChatInput" 
          placeholder="Ask a technical question about the architecture, schemas, or flows..." 
          class="flex-1 px-4 py-3 rounded-xl text-xs md:text-sm font-mono-telemetry border focus:outline-none"
          style="background: var(--input-bg); border-color: var(--card-border); color: var(--text-main);"
          onkeydown="if(event.key === 'Enter') executeRAGChatQuery();"
        />
        <button 
          onclick="executeRAGChatQuery()" 
          id="ragChatSendBtn"
          class="px-5 py-3 rounded-xl font-bold text-xs font-mono-telemetry tracking-wider uppercase transition-all shadow-md flex items-center space-x-1.5 hover:opacity-90 active:scale-95"
          style="background: var(--accent-gold); color: #000;"
        >
          <span>SEND</span>
          <span>✦</span>
        </button>
      </div>
    </div>
"""

if 'id="view-chat"' not in content:
    # Insert right before the closing </main> or after #view-specs
    content = content.replace('    <!-- VIEW 2: FULL SPECIFICATIONS & BLUEPRINTS STUDIO -->', chat_view_html + '\n    <!-- VIEW 2: FULL SPECIFICATIONS & BLUEPRINTS STUDIO -->')
    print("Inserted #view-chat UI canvas into DOM")

# =============================================================================
# 3. FIX COUNCIL CHAMBER ORBITAL MASH & SEAT SEPARATION
# =============================================================================
old_orbit = """      <!-- Dynamic Council Orbit Diagram -->
      <div class="relative w-full h-[260px] flex items-center justify-center mb-4 overflow-hidden">
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

new_orbit = """      <!-- Dynamic Council Orbit Diagram (De-Cramped & Generously Spaced) -->
      <div class="relative w-full h-[360px] flex items-center justify-center mb-6 overflow-hidden">
        <div class="absolute w-[520px] h-[260px] rounded-[100%] border pointer-events-none" style="border-color: var(--card-border);"></div>
        <div class="absolute w-80 h-80 rounded-full pointer-events-none opacity-15" style="background: radial-gradient(circle, var(--accent-gold) 0%, transparent 70%);"></div>

        <!-- Center Hub with Clean Vertical Clearance -->
        <div class="text-center z-10 px-4 max-w-xs pointer-events-none mt-6">
          <div class="text-[10px] font-mono-telemetry uppercase tracking-widest text-amber-400 font-bold">COUNCIL SEATS</div>
          <div class="text-lg sm:text-xl font-medium tracking-tight mt-1" style="color: var(--text-main);">Multi-Agent DAG</div>
          <div class="text-xs font-serif-luxury italic mt-0.5" style="color: var(--text-muted);">Specialized Autonomous Deliberation</div>
          <div class="mt-3 inline-flex items-center space-x-1.5 px-3.5 py-1 rounded-full text-[10px] font-mono-telemetry border" style="border-color: var(--card-border); background: var(--card-bg); color: var(--accent-gold);">
            <span class="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
            <span id="councilStatusText">STATUS: READY</span>
          </div>
        </div>"""

if old_orbit in content:
    content = content.replace(old_orbit, new_orbit)
    print("De-cramped Council Chamber orbital ring and separated center hub")

# Also update the seat IDs so they have explicit IDs and active highlight styles
old_strat_seat = """        <!-- Seat 1: Strategist (Top Center) -->
        <div 
          onclick="selectSeat('Strategist', 'Qwen 27B / Llama 3.3', 'Principal PM', 'Synthesizes strategic PRD, user personas, non-functional SLAs, and STRIDE security boundaries.', 'DAG STAGE 1')" 
          class="seat-station absolute top-2 left-1/2 transform -translate-x-1/2 text-center cursor-pointer group transition-transform hover:scale-105"
        >"""

new_strat_seat = """        <!-- Seat 1: Strategist (Top Center) -->
        <div 
          id="seat-station-strategist"
          onclick="selectSeat('Strategist', 'GPT-OSS-120B', 'Principal PM', 'Synthesizes strategic PRD, user personas, non-functional SLAs, and STRIDE security boundaries.', 'STAGE 1 // STRATEGY')" 
          class="seat-station absolute top-2 left-1/2 transform -translate-x-1/2 text-center cursor-pointer group transition-transform hover:scale-105 z-20"
        >"""

if old_strat_seat in content:
    content = content.replace(old_strat_seat, new_strat_seat)
    print("Updated Strategist seat element")

# =============================================================================
# 4. OVERHAUL formatMarkdown WITH CLEAN CODE EXTRACTION & TABLE PARSER
# =============================================================================
old_format_md = """    // 4. Markdown Formatting Engine (Fully Adaptive to Onyx True Black & Vellum Light)
    function formatMarkdown(text) {
      if (!text) return '';
      let html = text
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;');
      
      // Code blocks ```lang ... ```
      html = html.replace(/```([a-zA-Z0-9_\\-\\.]*)\\n([\\s\\S]*?)```/g, (match, lang, code) => {
        const cleanLang = (lang || '').toLowerCase().trim();
        const trimmedCode = code.trim();
        if (cleanLang === 'mermaid') {
          return `<div class="my-6 rounded-xl border overflow-hidden shadow-lg" style="border-color: var(--card-border); background: var(--code-bg);">
            <div class="px-4 py-2 border-b flex items-center justify-between text-[10px] font-mono-telemetry" style="border-color: var(--card-border); background: var(--bezel-bg); color: var(--text-muted);">
              <span class="uppercase font-bold tracking-wider flex items-center gap-1.5" style="color: var(--accent-gold);">
                <span>🗺️</span> MERMAID ARCHITECTURAL DIAGRAM
              </span>
              <button onclick="navigator.clipboard.writeText(this.getAttribute('data-code')); showToast('Mermaid syntax copied to clipboard');" data-code="${trimmedCode.replace(/"/g, '&quot;')}" class="hover:opacity-100 transition-opacity font-bold">COPY SYNTAX</button>
            </div>
            <div class="p-4 md:p-6 overflow-x-auto flex justify-center">
              <div class="mermaid text-center">${trimmedCode}</div>
            </div>
          </div>`;
        }
        return `<div class="my-5 rounded-xl border overflow-hidden" style="border-color: var(--card-border); background: var(--code-bg);">
          <div class="px-4 py-2 border-b flex items-center justify-between text-[10px] font-mono-telemetry" style="border-color: var(--card-border); background: var(--bezel-bg); color: var(--text-muted);">
            <span class="uppercase font-semibold tracking-wider" style="color: var(--accent-gold);">${lang || 'CODE'}</span>
            <button onclick="navigator.clipboard.writeText(this.parentElement.nextElementSibling.innerText); showToast('Code copied to clipboard');" class="hover:opacity-100 transition-opacity font-bold">COPY</button>
          </div>
          <pre class="p-4 md:p-5 overflow-x-auto text-xs font-mono-telemetry leading-relaxed" style="color: var(--code-text);"><code>${trimmedCode}</code></pre>
        </div>`;
      });

      // Headers
      html = html.replace(/^### (.*$)/gim, '<h3 class="text-base font-semibold mt-6 mb-2 tracking-wide" style="color: var(--text-main);">$1</h3>');
      html = html.replace(/^## (.*$)/gim, '<h2 class="text-lg font-semibold mt-8 mb-3 tracking-wide pb-2 border-b" style="color: var(--text-main); border-color: var(--card-border);">$1</h2>');
      html = html.replace(/^# (.*$)/gim, '<h1 class="text-2xl md:text-3xl font-light mt-8 mb-4 tracking-tight font-serif-luxury italic pb-3 border-b" style="color: var(--accent-gold); border-color: var(--card-border);">$1</h1>');

      // Bold & Italics
      html = html.replace(/\\*\\*(.*?)\\*\\*/g, '<strong class="font-semibold" style="color: var(--text-main);">$1</strong>');
      html = html.replace(/\\*(.*?)\\*/g, '<em class="italic" style="color: var(--text-muted);">$1</em>');

      // Checkboxes
      html = html.replace(/- \\[x\\] (.*$)/gim, '<div class="flex items-center space-x-2.5 py-1 text-xs font-mono-telemetry" style="color: var(--text-main);"><span class="text-amber-400 font-bold">☑</span> <span>$1</span></div>');
      html = html.replace(/- \\[ \\] (.*$)/gim, '<div class="flex items-center space-x-2.5 py-1 text-xs font-mono-telemetry" style="color: var(--text-muted);"><span class="opacity-60 font-bold">☐</span> <span>$1</span></div>');

      // Unordered list items
      html = html.replace(/^\\s*[-*]\\s+(.*$)/gim, '<li class="ml-5 list-disc text-xs md:text-sm py-1 leading-relaxed" style="color: var(--text-muted);">$1</li>');

      // Paragraphs
      html = html.replace(/\\n\\n+/g, '</p><p class="text-xs md:text-sm leading-relaxed my-3" style="color: var(--text-muted);">');

      return `<div class="space-y-4 font-light">${html}</div>`;
    }"""

new_format_md = """    // 4. Overhauled Markdown Engine: Safe Code Extraction + Markdown Tables + Pure Mermaid
    function formatMarkdown(text) {
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

      // 3. Headers, Bold, Italics, Lists
      processed = processed.replace(/^### (.*$)/gim, '<h3 class="text-base font-semibold mt-6 mb-2 tracking-wide" style="color: var(--text-main);">$1</h3>');
      processed = processed.replace(/^## (.*$)/gim, '<h2 class="text-lg font-semibold mt-8 mb-3 tracking-wide pb-2 border-b" style="color: var(--text-main); border-color: var(--card-border);">$1</h2>');
      processed = processed.replace(/^# (.*$)/gim, '<h1 class="text-2xl md:text-3xl font-light mt-8 mb-4 tracking-tight font-serif-luxury italic pb-3 border-b" style="color: var(--accent-gold); border-color: var(--card-border);">$1</h1>');
      processed = processed.replace(/\\*\\*(.*?)\\*\\*/g, '<strong class="font-semibold" style="color: var(--text-main);">$1</strong>');
      processed = processed.replace(/\\*(.*?)\\*/g, '<em class="italic" style="color: var(--text-muted);">$1</em>');
      processed = processed.replace(/- \\[x\\] (.*$)/gim, '<div class="flex items-center space-x-2.5 py-1 text-xs font-mono-telemetry" style="color: var(--text-main);"><span class="text-amber-400 font-bold">☑</span> <span>$1</span></div>');
      processed = processed.replace(/- \\[ \\] (.*$)/gim, '<div class="flex items-center space-x-2.5 py-1 text-xs font-mono-telemetry" style="color: var(--text-muted);"><span class="opacity-60 font-bold">☐</span> <span>$1</span></div>');
      processed = processed.replace(/^\\s*[-*]\\s+(.*$)/gim, '<li class="ml-5 list-disc text-xs md:text-sm py-1 leading-relaxed" style="color: var(--text-muted);">$1</li>');
      processed = processed.replace(/\\n\\n+/g, '</p><p class="text-xs md:text-sm leading-relaxed my-3" style="color: var(--text-muted);">');

      // 4. Safely re-inject Code Blocks (Pure text for Mermaid without tag leakage)
      codeBlocks.forEach((block, idx) => {
        const placeholder = `___VOGEN_CODE_BLOCK_${idx}___`;
        let replacement = '';
        const encodedCode = encodeURIComponent(block.code);
        
        if (block.lang === 'mermaid') {
          replacement = `<div class="my-6 rounded-xl border overflow-hidden shadow-lg" style="border-color: var(--card-border); background: var(--code-bg);">
            <div class="px-4 py-2 border-b flex items-center justify-between text-[10px] font-mono-telemetry" style="border-color: var(--card-border); background: var(--bezel-bg); color: var(--text-muted);">
              <span class="uppercase font-bold tracking-wider flex items-center gap-1.5" style="color: var(--accent-gold);">
                <span>🗺️</span> MERMAID ARCHITECTURAL DIAGRAM
              </span>
              <button onclick="navigator.clipboard.writeText(decodeURIComponent('${encodedCode}')); showToast('Mermaid syntax copied to clipboard');" class="hover:opacity-100 transition-opacity font-bold">COPY SYNTAX</button>
            </div>
            <div class="p-4 md:p-6 overflow-x-auto flex justify-center">
              <pre class="mermaid text-center" style="background: transparent;">${block.code}</pre>
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
        processed = processed.replace(placeholder, replacement);
      });

      return `<div class="space-y-4 font-light">${processed}</div>`;
    }"""

if old_format_md in content:
    content = content.replace(old_format_md, new_format_md)
    print("Overhauled formatMarkdown with safe code extraction & markdown table parser")

# =============================================================================
# 5. EXPAND switchView TO HANDLE 'chat' VIEW
# =============================================================================
old_switch_view = """    function switchView(viewName) {
      currentView = viewName;
      const landing = document.getElementById('view-landing');
      const specs = document.getElementById('view-specs');
      const navLanding = document.getElementById('nav-landing');
      const navSpecs = document.getElementById('nav-specs');"""

new_switch_view = """    function switchView(viewName) {
      currentView = viewName;
      const landing = document.getElementById('view-landing');
      const specs = document.getElementById('view-specs');
      const chat = document.getElementById('view-chat');
      const navLanding = document.getElementById('nav-landing');
      const navSpecs = document.getElementById('nav-specs');
      const navChat = document.getElementById('nav-chat');
      
      if (chat) chat.classList.add('hidden');"""

if old_switch_view in content:
    content = content.replace(old_switch_view, new_switch_view)
    print("Updated switchView to register 'chat' canvas")

# Also update the view active branch in switchView
old_view_logic = """      if (viewName === 'landing') {
        landing.classList.remove('hidden');
        specs.classList.add('hidden');
        navLanding.style.color = 'var(--text-main)';
        navLanding.style.borderBottom = '2px solid var(--accent-gold)';
        navSpecs.style.color = 'var(--text-muted)';
        navSpecs.style.borderBottom = 'none';
      } else {
        landing.classList.add('hidden');
        specs.classList.remove('hidden');
        navSpecs.style.color = 'var(--text-main)';
        navSpecs.style.borderBottom = '2px solid var(--accent-gold)';
        navLanding.style.color = 'var(--text-muted)';
        navLanding.style.borderBottom = 'none';
        renderCurrentDocTab();
      }"""

new_view_logic = """      if (viewName === 'landing') {
        landing.classList.remove('hidden');
        specs.classList.add('hidden');
        if (chat) chat.classList.add('hidden');
        navLanding.style.color = 'var(--text-main)';
        navLanding.style.borderBottom = '2px solid var(--accent-gold)';
        navSpecs.style.color = 'var(--text-muted)';
        navSpecs.style.borderBottom = 'none';
        if (navChat) { navChat.style.color = 'var(--text-muted)'; navChat.style.borderBottom = 'none'; }
      } else if (viewName === 'chat') {
        landing.classList.add('hidden');
        specs.classList.add('hidden');
        if (chat) chat.classList.remove('hidden');
        if (navChat) { navChat.style.color = 'var(--text-main)'; navChat.style.borderBottom = '2px solid var(--accent-gold)'; }
        navLanding.style.color = 'var(--text-muted)';
        navLanding.style.borderBottom = 'none';
        navSpecs.style.color = 'var(--text-muted)';
        navSpecs.style.borderBottom = 'none';
        const input = document.getElementById('ragChatInput');
        if (input) input.focus();
      } else {
        landing.classList.add('hidden');
        specs.classList.remove('hidden');
        if (chat) chat.classList.add('hidden');
        navSpecs.style.color = 'var(--text-main)';
        navSpecs.style.borderBottom = '2px solid var(--accent-gold)';
        navLanding.style.color = 'var(--text-muted)';
        navLanding.style.borderBottom = 'none';
        if (navChat) { navChat.style.color = 'var(--text-muted)'; navChat.style.borderBottom = 'none'; }
        renderCurrentDocTab();
      }"""

if old_view_logic in content:
    content = content.replace(old_view_logic, new_view_logic)
    print("Updated switchView branches for landing, specs, and chat")

# =============================================================================
# 6. ADD RAG CHAT LOGIC (executeRAGChatQuery, sendQuickPrompt, clearChatHistory)
# =============================================================================
rag_chat_js = """
    // =========================================================================
    // 7. Interactive RAG Architecture Chat Client
    // =========================================================================
    async function executeRAGChatQuery() {
      const input = document.getElementById('ragChatInput');
      const timeline = document.getElementById('ragChatTimeline');
      if (!input || !timeline) return;

      const query = input.value.trim();
      if (!query) return;
      input.value = '';

      // 1. Append User Message to Timeline
      const userBubble = document.createElement('div');
      userBubble.className = 'flex items-start justify-end space-x-3';
      userBubble.innerHTML = `
        <div class="space-y-1 max-w-2xl text-right">
          <div class="text-[10px] font-mono-telemetry font-semibold uppercase tracking-wider" style="color: var(--text-muted);">YOU // ARCHITECT</div>
          <div class="p-3.5 rounded-2xl border text-xs md:text-sm leading-relaxed inline-block text-left" style="background: var(--input-bg); border-color: var(--card-border); color: var(--text-main);">
            ${query.replace(/</g, '&lt;').replace(/>/g, '&gt;')}
          </div>
        </div>
        <div class="w-8 h-8 rounded-xl flex items-center justify-center shrink-0 font-mono-telemetry text-xs font-bold border" style="border-color: var(--accent-gold); background: var(--card-bg); color: var(--accent-gold);">
          U
        </div>
      `;
      timeline.appendChild(userBubble);

      // 2. Append Loading Placeholder for Assistant
      const loadingBubble = document.createElement('div');
      loadingBubble.className = 'flex items-start space-x-3';
      loadingBubble.id = 'ragLoadingIndicator';
      loadingBubble.innerHTML = `
        <div class="w-8 h-8 rounded-xl flex items-center justify-center shrink-0 font-mono-telemetry text-xs font-bold" style="background: var(--accent-gold); color: #000;">
          AI
        </div>
        <div class="p-3.5 rounded-2xl border text-xs font-mono-telemetry animate-pulse" style="background: var(--bezel-bg); border-color: var(--card-border); color: var(--accent-gold);">
          Retrieving grounded BM25 context &amp; querying model...
        </div>
      `;
      timeline.appendChild(loadingBubble);
      timeline.scrollTop = timeline.scrollHeight;

      try {
        const byokKey = localStorage.getItem('vogenflow_byok_key') || null;
        const res = await fetch(`${API_BASE}/api/rag/query`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            query: query,
            top_k: 3,
            byok_key: byokKey
          })
        });

        const loadingElem = document.getElementById('ragLoadingIndicator');
        if (loadingElem) loadingElem.remove();

        if (!res.ok) {
          const errData = await res.json().catch(() => ({ detail: 'Query failed' }));
          throw new Error(errData.detail || 'RAG query failed');
        }

        const data = await res.json();
        const answer = data.answer || "I could not find a grounded answer for this query in the indexed specifications.";
        const sources = data.sources || [];

        // Build sources citation pills
        let citationsHtml = '';
        if (sources.length > 0) {
          citationsHtml = `<div class="mt-2.5 pt-2 border-t flex flex-wrap gap-1.5" style="border-color: var(--card-border);">
            <span class="text-[9px] font-mono-telemetry uppercase text-amber-400 font-bold self-center">CITATIONS:</span>
            ${sources.map(s => `<span class="px-2 py-0.5 rounded text-[9px] font-mono-telemetry border" style="border-color: var(--card-border); background: var(--card-bg); color: var(--text-muted);">${s}</span>`).join('')}
          </div>`;
        }

        const aiBubble = document.createElement('div');
        aiBubble.className = 'flex items-start space-x-3';
        aiBubble.innerHTML = `
          <div class="w-8 h-8 rounded-xl flex items-center justify-center shrink-0 font-mono-telemetry text-xs font-bold" style="background: var(--accent-gold); color: #000;">
            AI
          </div>
          <div class="space-y-1.5 max-w-3xl">
            <div class="text-[10px] font-mono-telemetry font-semibold uppercase tracking-wider" style="color: var(--accent-gold);">
              VO-GEN-FLOW RAG ENGINE // ${data.model || 'OPENAI/GPT-OSS-120B'}
            </div>
            <div class="p-4 rounded-2xl border text-xs md:text-sm leading-relaxed" style="background: var(--bezel-bg); border-color: var(--card-border); color: var(--text-main);">
              <div>${formatMarkdown(answer)}</div>
              ${citationsHtml}
            </div>
          </div>
        `;
        timeline.appendChild(aiBubble);
      } catch (err) {
        const loadingElem = document.getElementById('ragLoadingIndicator');
        if (loadingElem) loadingElem.remove();

        const errBubble = document.createElement('div');
        errBubble.className = 'flex items-start space-x-3';
        errBubble.innerHTML = `
          <div class="w-8 h-8 rounded-xl flex items-center justify-center shrink-0 font-mono-telemetry text-xs font-bold bg-red-500 text-white">
            !
          </div>
          <div class="p-3.5 rounded-2xl border text-xs font-mono-telemetry text-red-400" style="background: var(--bezel-bg); border-color: var(--card-border);">
            Error querying RAG knowledge base: ${err.message}
          </div>
        `;
        timeline.appendChild(errBubble);
      }

      timeline.scrollTop = timeline.scrollHeight;
    }

    function sendQuickPrompt(promptText) {
      const input = document.getElementById('ragChatInput');
      if (input) {
        input.value = promptText.trim();
        executeRAGChatQuery();
      }
    }

    function clearChatHistory() {
      const timeline = document.getElementById('ragChatTimeline');
      if (timeline) {
        timeline.innerHTML = `
          <div class="flex items-start space-x-3">
            <div class="w-8 h-8 rounded-xl flex items-center justify-center shrink-0 font-mono-telemetry text-xs font-bold shadow-sm" style="background: var(--accent-gold); color: #000;">
              AI
            </div>
            <div class="space-y-1.5 max-w-3xl">
              <div class="text-[10px] font-mono-telemetry font-semibold uppercase tracking-wider" style="color: var(--accent-gold);">
                VO-GEN-FLOW RAG ENGINE // GROUNDED AGENT
              </div>
              <div class="p-4 rounded-2xl border text-xs md:text-sm leading-relaxed" style="background: var(--bezel-bg); border-color: var(--card-border); color: var(--text-main);">
                Chat history cleared. You can ask fresh questions about the architecture specifications or indexed codebases.
              </div>
            </div>
          </div>
        `;
        showToast('RAG Chat history cleared');
      }
    }
"""

if 'executeRAGChatQuery' not in content:
    content = content.replace('    // 5. Document Studio Content Data Store', rag_chat_js + '\n    // 5. Document Studio Content Data Store')
    print("Added executeRAGChatQuery & RAG Chat client logic")

# =============================================================================
# 7. ENHANCE selectSeat() WITH DYNAMIC HIGHLIGHT & THOUGHT SELECTION
# =============================================================================
old_select_seat_head = """    function selectSeat(name, model, role, desc, stage) {
      const badge = document.getElementById('seatInspectorBadge');"""

new_select_seat_head = """    function selectSeat(name, model, role, desc, stage) {
      // Dynamic visual highlight on clicked station
      document.querySelectorAll('.seat-station').forEach(el => el.classList.remove('ring-2', 'ring-amber-400', 'rounded-2xl'));
      const activeEl = document.getElementById(`seat-station-${name.toLowerCase().replace('the ', '').trim()}`);
      if (activeEl) activeEl.classList.add('ring-2', 'ring-amber-400', 'rounded-2xl');

      const badge = document.getElementById('seatInspectorBadge');"""

if old_select_seat_head in content:
    content = content.replace(old_select_seat_head, new_select_seat_head)
    print("Added dynamic active seat highlight in selectSeat")

# Write out changes
INDEX_PATH.write_text(content, encoding="utf-8")
DEMO_PATH.write_text(content, encoding="utf-8")
print(f"Master rethink patch written to {INDEX_PATH} and mirrored to {DEMO_PATH}")
