import re

def update_index_html():
    with open('web_app/index.html', 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Add .architectural-canvas to CSS if not present
    if '.architectural-canvas' not in content:
        css_needle = '.font-serif-luxury { font-family: var(--font-serif); }'
        canvas_css = """
    /* Architectural CAD Dot Grid Canvas */
    .architectural-canvas {
      background-color: var(--bg-color);
      background-image: radial-gradient(circle, rgba(212, 175, 55, 0.12) 1px, transparent 1px);
      background-size: 26px 26px;
    }
    body.theme-vellum .architectural-canvas {
      background-image: radial-gradient(circle, rgba(184, 134, 11, 0.16) 1px, transparent 1px);
    }
"""
        content = content.replace(css_needle, canvas_css + "\n    " + css_needle)

    # 2. Re-engineer VIEW 1: LANDING PAGE
    p1 = content.find('<!-- ========================================================================= -->\n  <!-- VIEW 1: LANDING PAGE')
    p2 = content.find('<!-- ========================================================================= -->\n  <!-- VIEW 2: ENGINEERING STUDIO')
    assert p1 != -1 and p2 != -1, "Landing section markers not found"

    new_landing = """<!-- ========================================================================= -->
  <!-- VIEW 1: LANDING PAGE (Spacious Overview & Immediate Synthesis Console)    -->
  <!-- ========================================================================= -->
  <div id="view-landing" class="view-panel max-w-[1600px] mx-auto w-full space-y-12 pb-44">
    
    <!-- Hero Section -->
    <section class="monolith-bezel rounded-2xl p-10 md:p-16 text-center relative overflow-hidden">
      <div class="max-w-4xl mx-auto space-y-8 z-10 relative">
        <div class="inline-flex items-center space-x-2 px-4 py-1.5 rounded-full text-[11px] font-mono-telemetry uppercase tracking-wider gold-badge">
          <span>VOICE-TO-PRODUCTION COGNITIVE ARCHITECTURE STUDIO</span>
        </div>
        <h1 class="text-4xl md:text-6xl font-normal tracking-tight leading-tight" style="color: var(--text-main);">
          Speak to Architect. <br>
          <span class="font-serif-luxury italic text-amber-400 font-light" style="color: var(--accent-gold);">Synthesize Production Blueprints in Seconds.</span>
        </h1>
        <p class="text-xs md:text-base font-light max-w-3xl mx-auto leading-relaxed text-neutral-400" style="color: var(--text-muted);">
          Vo-Gen-Flow translates unstructured spoken brainstorming, technical voice memos, and system debates into production-grade PRDs, C4 Mermaid topologies, PostgreSQL DDL schemas, and executable delivery checklists.
        </p>

        <!-- Primary Architectural Synthesis Console (Centerpiece) -->
        <div class="monolith-card rounded-2xl p-3 md:p-5 border shadow-2xl space-y-4 max-w-3xl mx-auto mt-6 text-left" style="background: var(--card-bg); border-color: var(--bezel-border);">
          <div class="flex flex-col sm:flex-row items-center gap-3">
            <!-- Dictate / Voice Record Button -->
            <button 
              id="heroMicBtn" 
              onclick="toggleMicStream()" 
              class="px-4 py-3 rounded-xl border text-xs font-mono-telemetry flex items-center space-x-2 transition-all hover:border-amber-400 group shrink-0"
              style="background: var(--input-bg); border-color: var(--card-border); color: var(--text-main);"
              title="Click to Dictate Architecture Requirements"
            >
              <div class="w-3 h-3 rounded-full bg-red-500/80 group-hover:animate-ping"></div>
              <span class="text-[11px] font-bold tracking-wider uppercase text-neutral-300">DICTATE</span>
            </button>

            <!-- Architectural Prompt Input Field -->
            <div class="relative flex-1 w-full">
              <input 
                type="text" 
                id="landingPromptInput" 
                placeholder="Describe your system (e.g. 'Global payment gateway with Redis Redlock and PostgreSQL 16 double-entry ledger')..." 
                class="w-full px-4 py-3 rounded-xl text-xs md:text-sm font-light border focus:outline-none transition-colors"
                style="background: var(--input-bg); border-color: var(--card-border); color: var(--text-main);"
                onkeydown="if(event.key === 'Enter') triggerGenerate();"
              />
            </div>

            <!-- Convene Council & Generate Action Button -->
            <button 
              onclick="triggerGenerate()" 
              class="w-full sm:w-auto px-6 py-3 rounded-xl font-semibold text-xs font-mono-telemetry tracking-wider uppercase transition-all shadow-xl flex items-center justify-center space-x-2 shrink-0 hover:opacity-95 transform active:scale-95"
              style="background: var(--accent-gold); color: #000;"
            >
              <span>CONVENE COUNCIL &amp; GENERATE</span>
              <span class="text-sm">✦</span>
            </button>
          </div>

          <!-- Quick One-Click Architectural Archetypes -->
          <div class="pt-1 flex flex-wrap items-center gap-2 text-[10px] font-mono-telemetry" style="color: var(--text-muted);">
            <span class="uppercase font-semibold tracking-wider text-neutral-400">ARCHETYPES:</span>
            <button onclick="setArchetypeAndGenerate('payments')" class="px-2.5 py-1 rounded-lg border hover:border-amber-400 hover:text-amber-300 transition-colors" style="background: var(--input-bg); border-color: var(--card-border); color: var(--text-main);">⚡ Payments Gateway</button>
            <button onclick="setArchetypeAndGenerate('webrtc')" class="px-2.5 py-1 rounded-lg border hover:border-amber-400 hover:text-amber-300 transition-colors" style="background: var(--input-bg); border-color: var(--card-border); color: var(--text-main);">🔄 WebRTC Audio Streamer</button>
            <button onclick="setArchetypeAndGenerate('saas')" class="px-2.5 py-1 rounded-lg border hover:border-amber-400 hover:text-amber-300 transition-colors" style="background: var(--input-bg); border-color: var(--card-border); color: var(--text-main);">📦 Multi-Tenant SaaS with RLS</button>
            <button onclick="setArchetypeAndGenerate('zerotrust')" class="px-2.5 py-1 rounded-lg border hover:border-amber-400 hover:text-amber-300 transition-colors" style="background: var(--input-bg); border-color: var(--card-border); color: var(--text-main);">🛡 Zero-Trust Envoy Mesh</button>
            <button onclick="setArchetypeAndGenerate('kafka')" class="px-2.5 py-1 rounded-lg border hover:border-amber-400 hover:text-amber-300 transition-colors" style="background: var(--input-bg); border-color: var(--card-border); color: var(--text-main);">📊 Kafka Event Stream</button>
          </div>
        </div>

        <!-- Quick Secondary Links -->
        <div class="pt-4 flex flex-wrap justify-center items-center gap-6 text-xs font-mono-telemetry" style="color: var(--text-muted);">
          <button onclick="switchView('studio')" class="hover:text-amber-300 transition-colors flex items-center space-x-1.5">
            <span>Open Engineering Studio</span>
            <span>→</span>
          </button>
          <span>•</span>
          <button onclick="switchView('specs')" class="hover:text-amber-300 transition-colors flex items-center space-x-1.5">
            <span>Inspect Production Specifications</span>
            <span>→</span>
          </button>
          <span>•</span>
          <button onclick="toggleCouncilModal()" class="hover:text-amber-300 transition-colors flex items-center space-x-1.5 text-amber-400">
            <span>Inspect Council Protocol [C]</span>
            <span>→</span>
          </button>
        </div>
      </div>
    </section>

    <!-- Pre-Recorded Audio File Upload Dropzone (Secondary Option) -->
    <section class="monolith-bezel rounded-2xl p-8 text-center relative max-w-4xl mx-auto">
      <div 
        id="landingDropZone" 
        class="border-2 border-dashed rounded-xl p-8 md:p-10 transition-all cursor-pointer flex flex-col items-center justify-center space-y-3"
        style="border-color: var(--bezel-border); background: var(--input-bg);"
        onclick="document.getElementById('audioFileInput').click()"
        ondragover="handleDragOver(event)"
        ondragleave="handleDragLeave(event)"
        ondrop="handleFileDrop(event)"
      >
        <input 
          type="file" 
          id="audioFileInput" 
          class="hidden" 
          accept=".wav,.mp3,.m4a,.ogg,.webm,.flac" 
          onchange="handleFileSelect(event)" 
        />
        
        <div class="w-12 h-12 rounded-full border border-amber-400/30 flex items-center justify-center text-amber-400 group-hover:scale-110 transition-transform" style="background: rgba(212,175,55,0.08);">
          <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
          </svg>
        </div>

        <div>
          <h3 class="text-sm md:text-base font-semibold" style="color: var(--text-main);">Drop Technical Audio Note or Click to Browse</h3>
          <p class="text-xs font-light mt-1" style="color: var(--text-muted);">
            Supports .WAV, .MP3, .M4A, .OGG, .WEBM up to 25MB. Automatically transcribes and convenes the Council.
          </p>
        </div>

        <div id="uploadFileStatus" class="text-xs font-mono-telemetry text-amber-400 hidden pt-2">
          Uploading &amp; Transcribing...
        </div>
      </div>
    </section>

    <!-- Core Value Matrix: 3 Architectural Pillars -->
    <section class="grid grid-cols-1 md:grid-cols-3 gap-8">
      <div class="monolith-card rounded-2xl p-8 space-y-4">
        <div class="text-[10px] font-mono-telemetry uppercase tracking-wider text-emerald-400">PILLAR 01 // SUB-400MS STT</div>
        <h3 class="text-xl font-medium" style="color: var(--text-main);">Acoustic Intelligence</h3>
        <p class="text-xs md:text-sm font-light leading-relaxed" style="color: var(--text-muted);">
          Groq Whisper LPU speech processing engine captures natural pacing, technical abbreviations, and architectural terminology with noise cancellation.
        </p>
      </div>

      <div class="monolith-card rounded-2xl p-8 space-y-4">
        <div class="text-[10px] font-mono-telemetry uppercase tracking-wider" style="color: var(--accent-gold);">PILLAR 02 // UNIVERSAL RAG</div>
        <h3 class="text-xl font-medium" style="color: var(--text-main);">Curated Architecture Blueprints</h3>
        <p class="text-xs md:text-sm font-light leading-relaxed" style="color: var(--text-muted);">
          Grounds conversations against 16 battle-tested blueprints spanning Kafka streaming, WebRTC, Kubernetes, and PostgreSQL Row-Level Security.
        </p>
      </div>

      <div class="monolith-card rounded-2xl p-8 space-y-4">
        <div class="text-[10px] font-mono-telemetry uppercase tracking-wider text-amber-400">PILLAR 03 // MULTI-AGENT COUNCIL</div>
        <h3 class="text-xl font-medium" style="color: var(--text-main);">Specialist Consensus Deliberation</h3>
        <p class="text-xs md:text-sm font-light leading-relaxed" style="color: var(--text-muted);">
          Routes PRD strategy to Product Strategists, database DDL to Systems Architects, and delivery tasks to Agile Leads with automated consensus verification.
        </p>
      </div>
    </section>
  </div>

  """

    content = content[:p1] + new_landing + content[p2:]

    # 3. Re-engineer VIEW 2: STUDIO (Remove rigid 82vh, add prompt bar, spacious canvas)
    p2 = content.find('<!-- ========================================================================= -->\n  <!-- VIEW 2: ENGINEERING STUDIO')
    p3 = content.find('<!-- ========================================================================= -->\n  <!-- VIEW 3: SPECIFICATION')
    assert p2 != -1 and p3 != -1, "Studio section markers not found"

    new_studio = """<!-- ========================================================================= -->
  <!-- VIEW 2: ENGINEERING STUDIO (Spacious Architectural Workspace)             -->
  <!-- ========================================================================= -->
  <div id="view-studio" class="view-panel monolith-bezel w-full max-w-[1600px] mx-auto rounded-2xl flex flex-col min-h-[780px] relative pb-6 hidden space-y-4">

    <div class="flex-1 grid grid-cols-12 relative rounded-2xl overflow-hidden border" style="border-color: var(--card-border);">

      <!-- Column 1: Workspace & Real Session History (3 Cols) -->
      <aside class="col-span-12 lg:col-span-3 border-r p-5 md:p-6 flex flex-col justify-between overflow-y-auto" style="border-color: var(--card-border); background: var(--input-bg);">
        <div class="space-y-5">
          <div class="flex items-center justify-between text-[11px] font-mono-telemetry uppercase" style="color: var(--text-muted);">
            <span>ACTIVE WORKSPACE</span>
            <button onclick="resetToNewSession()" class="font-bold hover:underline" style="color: var(--accent-gold);" title="New Session">+ NEW</button>
          </div>

          <!-- Active Session Card -->
          <div class="p-4 rounded-xl border text-xs font-mono-telemetry space-y-2" style="background: var(--card-bg); border-color: var(--bezel-border);">
            <div class="text-[9px] font-bold uppercase flex justify-between" style="color: var(--accent-gold);">
              <span>CURRENT SESSION</span>
              <span id="activeSessionBadge" class="text-emerald-400 font-bold">READY</span>
            </div>
            <div id="sidebarProjectTitle" class="font-medium text-sm truncate" style="color: var(--text-main);">Vo-Gen-Flow Core</div>
            <div class="text-[10px]" style="color: var(--text-subtle);" id="sidebarSessionId">ID: auto-generated</div>
            <div class="text-[10px] text-amber-400">ARCHITECTURE: C4 Level 2 Container</div>
            <div class="text-[10px] text-emerald-400">COUNCIL: 4 Specialist Seats</div>
          </div>

          <!-- Upload Audio Button in Studio -->
          <button 
            onclick="document.getElementById('studioAudioInput').click()" 
            class="w-full py-3 px-3 rounded-xl border text-xs font-mono-telemetry transition-all flex items-center justify-center space-x-2 group hover:border-amber-400"
            style="background: var(--card-bg); border-color: var(--card-border); color: var(--text-main);"
          >
            <input 
              type="file" 
              id="studioAudioInput" 
              accept=".wav,.mp3,.m4a,.ogg,.webm,.flac" 
              class="hidden" 
              onchange="handleFileSelect(event)" 
            />
            <svg class="w-4 h-4 text-amber-400 group-hover:scale-110 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
            </svg>
            <span class="font-medium">Upload Audio Note</span>
          </button>

          <!-- Repository Dropzone in Studio Sidebar -->
          <div 
            class="p-4 rounded-xl border border-dashed text-center cursor-pointer transition-all hover:border-amber-400"
            style="border-color: var(--bezel-border); background: var(--card-bg);"
            onclick="document.getElementById('sidebarDocInput').click()"
          >
            <input type="file" id="sidebarDocInput" class="hidden" accept=".md,.py,.sql,.json,.txt" onchange="handleDocUpload(event)" />
            <div class="text-[10px] font-mono-telemetry uppercase font-semibold" style="color: var(--accent-gold);">+ INDEX SPECIFICATION FILE</div>
            <div class="text-[9px] pt-1" style="color: var(--text-subtle);">Adds to local RAG context</div>
          </div>

          <!-- Past Session History -->
          <div class="space-y-2 pt-2">
            <div class="text-[10px] font-mono-telemetry uppercase tracking-wider" style="color: var(--text-subtle);">RECENT SESSIONS</div>
            <div id="recentSessionsList" class="space-y-1.5 max-h-48 overflow-y-auto text-xs font-mono-telemetry">
              <!-- Dynamically populated -->
            </div>
          </div>
        </div>
      </aside>

      <!-- Column 2: Central C4 Architecture Topology Canvas (6 Cols) -->
      <main class="col-span-12 lg:col-span-6 p-6 md:p-8 flex flex-col justify-between relative overflow-hidden" style="background: var(--bg-color);">
        
        <!-- Header Info & Live Architectural Prompt Console -->
        <div class="space-y-3 z-10 border-b pb-4" style="border-color: var(--card-border);">
          <div class="flex justify-between items-center">
            <div>
              <h2 id="studioProjectTitle" class="text-base md:text-lg font-medium flex items-center space-x-2" style="color: var(--text-main);">
                <span>Voice Architecture Project</span>
                <span class="text-xs font-mono-telemetry" style="color: var(--text-subtle);">// C4 TOPOLOGY</span>
              </h2>
              <p class="text-[10px] font-mono-telemetry" style="color: var(--text-muted);">Autonomous multi-agent consensus visualizer</p>
            </div>
            <div class="flex space-x-2">
              <button onclick="toggleCouncilModal()" class="px-3 py-1.5 rounded-lg border text-xs font-mono-telemetry gold-badge font-semibold" title="Inspect Multi-Agent Council Protocol">
                Council Seats [C]
              </button>
              <button onclick="switchView('specs')" class="px-3 py-1.5 rounded-lg border text-xs font-mono-telemetry hover:border-amber-400" style="background: var(--card-bg); border-color: var(--card-border); color: var(--text-main);">
                Inspect PRD &amp; DDL
              </button>
            </div>
          </div>

          <!-- Quick In-Studio Architectural Synthesis Prompt Bar -->
          <div class="flex items-center gap-2 pt-1">
            <input 
              type="text" 
              id="studioPromptInput" 
              placeholder="Refine architecture prompt or speak to generate..." 
              class="flex-1 px-3.5 py-2 rounded-xl text-xs font-mono-telemetry border focus:outline-none"
              style="background: var(--input-bg); border-color: var(--card-border); color: var(--text-main);"
              onkeydown="if(event.key === 'Enter') triggerGenerate();"
            />
            <button 
              onclick="triggerGenerate()" 
              class="px-4 py-2 rounded-xl text-xs font-mono-telemetry font-bold tracking-wider uppercase transition-all shadow-md flex items-center space-x-1.5 shrink-0 hover:opacity-90"
              style="background: var(--accent-gold); color: #000;"
            >
              <span>RECONVENE COUNCIL</span>
              <span>✦</span>
            </button>
          </div>
        </div>

        <!-- Interactive Architecture Nodes Matrix with Dot Grid CAD Canvas -->
        <div class="architectural-canvas rounded-xl border relative my-4 py-12 md:py-16 min-h-[480px] flex items-center justify-center overflow-hidden" style="border-color: var(--card-border);">
          <svg class="absolute inset-0 w-full h-full pointer-events-none" style="z-index: 1;">
            <line x1="22%" y1="32%" x2="50%" y2="32%" class="wire-glow" />
            <line x1="22%" y1="68%" x2="50%" y2="68%" class="wire-glow" />
            <line x1="50%" y1="32%" x2="78%" y2="50%" class="wire-glow" />
            <line x1="50%" y1="68%" x2="78%" y2="50%" class="wire-glow" />
          </svg>

          <div class="relative z-10 w-full flex justify-between items-center px-6 md:px-12">
            
            <!-- Ingestion Nodes -->
            <div class="space-y-16">
              <div onclick="inspectNode('Acoustic Stream', 'Microphone or uploaded audio note stream.')" class="monolith-node rounded-xl px-5 py-4 text-center min-w-[130px] cursor-pointer">
                <div class="text-[9px] font-mono-telemetry font-bold" style="color: var(--accent-gold);">AUDIO INGESTION</div>
                <div class="text-xs font-semibold mt-0.5" style="color: var(--text-main);">Acoustic Input</div>
              </div>
              <div onclick="inspectNode('Knowledge Catalog', '16 curated architectural blueprints &amp; user repo files.')" class="monolith-node rounded-xl px-5 py-4 text-center min-w-[130px] cursor-pointer">
                <div class="text-[9px] font-mono-telemetry font-bold" style="color: var(--text-subtle);">KNOWLEDGE DB</div>
                <div class="text-xs font-semibold mt-0.5" style="color: var(--text-main);">16 Blueprints</div>
              </div>
            </div>

            <!-- Processing Nodes -->
            <div class="space-y-16">
              <div onclick="inspectNode('Speech-to-Text', 'Sub-400ms acoustic transcription with noise filtering.')" class="monolith-node rounded-xl px-6 py-4 text-center min-w-[140px] cursor-pointer">
                <div class="text-[9px] font-mono-telemetry font-bold text-emerald-400">SPEECH ENGINE</div>
                <div class="text-xs font-semibold mt-0.5" style="color: var(--text-main);">Sub-400ms STT</div>
              </div>
              <div onclick="inspectNode('Universal RAG Engine', 'In-memory Okapi BM25 + dense semantic retrieval.')" class="monolith-node rounded-xl px-6 py-4 text-center min-w-[140px] cursor-pointer">
                <div class="text-[9px] font-mono-telemetry font-bold text-amber-400">RETRIEVAL</div>
                <div class="text-xs font-semibold mt-0.5" style="color: var(--text-main);">Pattern Grounding</div>
              </div>
            </div>

            <!-- Synthesis Output -->
            <div class="space-y-12">
              <div onclick="inspectNode('Multi-Model Council', 'Specialist multi-agent DAG consensus.')" class="monolith-node rounded-xl px-6 py-4 text-center min-w-[140px] cursor-pointer">
                <div class="text-[9px] font-mono-telemetry font-bold" style="color: var(--accent-gold);">MULTI-AGENT</div>
                <div class="text-xs font-semibold mt-0.5" style="color: var(--text-main);">Council Engine</div>
              </div>
              <div onclick="switchView('specs')" class="monolith-node rounded-xl px-6 py-4 text-center min-w-[140px] cursor-pointer">
                <div class="text-[9px] font-mono-telemetry font-bold text-amber-300">DELIVERABLES</div>
                <div class="text-xs font-semibold mt-0.5" style="color: var(--text-main);">PRD &amp; Schemas</div>
              </div>
            </div>

          </div>
        </div>

        <div class="text-[10px] font-mono-telemetry flex justify-between z-10 border-t pt-3" style="border-color: var(--card-border); color: var(--text-subtle);">
          <span id="activeModelTelemetry">COUNCIL CONSENSUS: Product Strategist + Lead Systems Architect</span>
          <span id="activeLatencyBudget">SPEED SLA: &lt; 2000MS</span>
        </div>
      </main>

      <!-- Column 3: Telemetry & Deliverables (3 Cols) -->
      <aside class="col-span-12 lg:col-span-3 border-l p-5 md:p-6 flex flex-col justify-between overflow-y-auto" style="border-color: var(--card-border); background: var(--input-bg);">
        <div class="space-y-5">
          <div class="flex items-center justify-between text-[11px] font-mono-telemetry uppercase" style="color: var(--text-muted);">
            <span>COUNCIL STATUS</span>
            <span id="pipelineStatusBadge" class="text-[10px] text-emerald-400 font-bold">READY</span>
          </div>

          <!-- Council Specialist Roster -->
          <div class="p-4 rounded-xl border space-y-2.5 text-xs font-mono-telemetry" style="background: var(--card-bg); border-color: var(--card-border);">
            <div class="flex justify-between text-[10px]">
              <span style="color: var(--text-muted);">Product Strategist:</span>
              <span class="font-medium" style="color: var(--text-main);">Principal PM</span>
            </div>
            <div class="flex justify-between text-[10px]">
              <span style="color: var(--text-muted);">System Architect:</span>
              <span class="font-medium" style="color: var(--accent-gold);">Lead Systems Architect</span>
            </div>
            <div class="flex justify-between text-[10px]">
              <span style="color: var(--text-muted);">Delivery Lead:</span>
              <span class="text-emerald-400 font-medium">Agile Delivery Lead</span>
            </div>
            <div class="flex justify-between text-[10px]">
              <span style="color: var(--text-muted);">Verification Gate:</span>
              <span class="text-amber-400 font-medium">Consensus Verifier</span>
            </div>
          </div>

          <!-- Dynamic Real-Time Project Logs -->
          <div class="space-y-2 pt-1">
            <div class="text-[10px] font-mono-telemetry uppercase tracking-wider" style="color: var(--text-subtle);">SYSTEM EVENT LOG</div>
            <div id="projectLogContainer" class="p-3 rounded-xl border font-mono-telemetry text-[9px] space-y-2 max-h-56 overflow-y-auto" style="background: var(--card-bg); border-color: var(--card-border); color: var(--text-muted);">
              <!-- Dynamically appended -->
            </div>
          </div>
        </div>

        <div class="pt-4 border-t flex space-x-2" style="border-color: var(--card-border);">
          <button onclick="exportGitScript()" class="flex-1 py-2.5 rounded-lg border text-xs font-mono-telemetry transition-all text-center hover:border-amber-400" style="background: var(--card-bg); border-color: var(--card-border); color: var(--text-main);">
            EXPORT GIT
          </button>
          <button onclick="switchView('specs')" class="flex-1 py-2.5 rounded-lg text-xs font-mono-telemetry font-bold transition-all text-center shadow-md" style="background: var(--accent-gold); color: #000;">
            VIEW SPECS
          </button>
        </div>
      </aside>

    </div>
  </div>

  """

    content = content[:p2] + new_studio + content[p3:]

    # 4. Re-engineer VIEW 3: SPECIFICATION & DOCUMENT STUDIO (Collapsible RAG Drawer, Spacious Document Container)
    p3 = content.find('<!-- ========================================================================= -->\n  <!-- VIEW 3: SPECIFICATION')
    p4 = content.find('<!-- ========================================================================= -->\n  <!-- WISPR FLOW INSPIRED')
    assert p3 != -1 and p4 != -1, "Specs section markers not found"

    new_specs = """<!-- ========================================================================= -->
  <!-- VIEW 3: SPECIFICATION & DOCUMENT STUDIO (PRD / Architecture / Tasks)      -->
  <!-- ========================================================================= -->
  <div id="view-specs" class="view-panel max-w-[1600px] mx-auto w-full space-y-6 pb-44 hidden">
    <div class="monolith-bezel rounded-2xl p-6 md:p-10 space-y-6">
      
      <!-- Doc Header Tabs -->
      <div class="flex flex-wrap items-center justify-between border-b pb-5 gap-4" style="border-color: var(--card-border);">
        <div>
          <div class="text-[10px] font-mono-telemetry uppercase tracking-widest" style="color: var(--accent-gold);">PUBLICATION STUDIO</div>
          <h2 class="text-xl md:text-2xl font-light" style="color: var(--text-main);">
            Specifications &amp; Schemas <span id="docProjectTitle" class="font-serif-luxury italic text-lg md:text-xl font-light" style="color: var(--accent-gold);">Active Session</span>
          </h2>
        </div>

        <div class="flex items-center space-x-2 p-1.5 rounded-xl border text-xs font-mono-telemetry" style="background: var(--card-bg); border-color: var(--card-border);">
          <button id="doc-prd" onclick="switchDocTab('prd')" class="px-4 py-2 rounded-lg font-medium" style="background: var(--input-bg); color: var(--text-main);">PRD.md</button>
          <button id="doc-arch" onclick="switchDocTab('arch')" class="px-4 py-2 rounded-lg hover:opacity-100" style="color: var(--text-muted);">architecture.md</button>
          <button id="doc-flow" onclick="switchDocTab('flow')" class="px-4 py-2 rounded-lg hover:opacity-100" style="color: var(--text-muted);">flow.md</button>
          <button id="doc-tasks" onclick="switchDocTab('tasks')" class="px-4 py-2 rounded-lg hover:opacity-100" style="color: var(--text-muted);">tasks.md</button>
        </div>

        <div class="flex space-x-3">
          <button onclick="copyAllSpecifications()" class="px-4 py-2.5 rounded-xl border text-xs font-mono-telemetry transition-all hover:border-amber-400" style="background: var(--card-bg); border-color: var(--card-border); color: var(--text-main);">
            COPY ALL SPECIFICATIONS
          </button>
          <button onclick="exportGitScript()" class="px-5 py-2.5 rounded-xl text-xs font-mono-telemetry font-bold transition-all shadow-md" style="background: var(--accent-gold); color: #000;">
            EXPORT GIT SCRIPT
          </button>
        </div>
      </div>

      <!-- Collapsible RAG Ingestion Header (Saves vertical room for documents) -->
      <div class="rounded-xl border transition-all" style="background: var(--card-bg); border-color: var(--card-border);">
        <div class="p-3.5 px-5 flex items-center justify-between cursor-pointer hover:opacity-95" onclick="toggleRagIngestionDrawer()">
          <div class="flex items-center space-x-3">
            <span class="text-xs font-mono-telemetry font-bold" style="color: var(--accent-gold);">✦ RAG KNOWLEDGE BASE</span>
            <span id="indexedDocsCount" class="text-[10px] font-mono-telemetry px-2.5 py-0.5 rounded gold-badge">
              16 Curated Blueprints Grounded
            </span>
          </div>
          <div class="flex items-center space-x-2 text-[11px] font-mono-telemetry" style="color: var(--text-muted);">
            <span id="ragToggleLabel">+ Ingest Custom Specs / Files</span>
            <span id="ragToggleIcon" class="text-xs">▼</span>
          </div>
        </div>

        <!-- Hidden by default to provide maximum breathing room for the actual documents -->
        <div id="ragIngestionDrawer" class="hidden p-5 border-t space-y-4" style="border-color: var(--card-border);">
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <!-- File Dropzone -->
            <div 
              id="specsDropZone" 
              class="border-2 border-dashed rounded-xl p-5 text-center cursor-pointer hover:border-amber-400 transition-all"
              style="border-color: var(--bezel-border); background: var(--input-bg);"
              onclick="document.getElementById('specsFileInput').click()"
              ondragover="handleSpecsDragOver(event)"
              ondragleave="handleSpecsDragLeave(event)"
              ondrop="handleSpecsDrop(event)"
            >
              <input type="file" id="specsFileInput" class="hidden" accept=".md,.py,.sql,.json,.txt" onchange="handleSpecsFileSelect(event)" />
              <div class="text-xs font-mono-telemetry font-medium" style="color: var(--text-main);">Drag &amp; Drop Specification or Code File</div>
              <div class="text-[10px] pt-1" style="color: var(--text-muted);">Instantly indexes chunks into Okapi BM25 &amp; Dense Vector Store</div>
            </div>
            <!-- Quick Text Indexer -->
            <div class="flex flex-col space-y-2">
              <textarea id="quickIndexText" placeholder="Paste architectural context or database schemas here to index immediately..." class="w-full h-20 p-3 rounded-lg border text-xs font-mono-telemetry resize-none focus:outline-none" style="background: var(--input-bg); border-color: var(--card-border); color: var(--text-main);"></textarea>
              <button onclick="indexQuickText()" class="self-end px-3.5 py-1.5 rounded-lg text-xs font-mono-telemetry font-semibold gold-badge hover:opacity-90">
                Index Custom Text
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Spacious Document Content Body -->
      <div id="docContentContainer" class="rounded-xl border p-8 md:p-12 text-sm font-light leading-relaxed space-y-5 min-h-[550px] pb-16 overflow-x-auto" style="background: var(--card-bg); border-color: var(--card-border); color: var(--text-main);">
        <!-- Injected via switchDocTab() -->
      </div>
    </div>
  </div>

  """

    content = content[:p3] + new_specs + content[p4:]

    # 5. Update Council Modal action button to triggerGenerate()
    modal_btn_old = """<button onclick="confirmCouncilRun()" class="px-4 py-1.5 rounded-lg font-semibold text-[11px] transition-colors shadow-md" style="background: var(--accent-gold); color: #000;">
            CONVENE NOW
          </button>"""
    modal_btn_new = """<button onclick="triggerGenerate()" class="px-5 py-2 rounded-xl font-semibold text-xs font-mono-telemetry transition-colors shadow-md flex items-center space-x-1.5" style="background: var(--accent-gold); color: #000;">
            <span>CONVENE COUNCIL &amp; GENERATE</span>
            <span>✦</span>
          </button>"""
    if modal_btn_old in content:
        content = content.replace(modal_btn_old, modal_btn_new)

    # 6. Add triggerGenerate, setArchetypeAndGenerate, and toggleRagIngestionDrawer in JS
    js_needle = "let isCouncilOpen = false;"
    new_js = """// Immediate Council Convening & Prompt Dispatch
    function triggerGenerate(customPrompt) {
      if (isCouncilOpen) toggleCouncilModal();
      
      let prompt = customPrompt;
      if (!prompt || typeof prompt !== 'string') {
        const landingInput = document.getElementById('landingPromptInput');
        const studioInput = document.getElementById('studioPromptInput');
        prompt = (landingInput && landingInput.value.trim()) || 
                 (studioInput && studioInput.value.trim()) || 
                 lastTranscript || 
                 'High-Throughput Global Payments Gateway & Distributed Ledger';
      }

      lastTranscript = prompt;

      // Synchronize input fields
      const landingInput = document.getElementById('landingPromptInput');
      const studioInput = document.getElementById('studioPromptInput');
      if (landingInput) landingInput.value = prompt;
      if (studioInput) studioInput.value = prompt;

      // Convene the council immediately!
      runCouncilDeliberation(prompt);
    }

    function setArchetypeAndGenerate(type) {
      const archetypes = {
        payments: 'High-throughput global payments gateway with Redis Redlock idempotency and PostgreSQL 16 double-entry ledger.',
        webrtc: 'Sub-50ms WebRTC voice room with selective forwarding unit SFU, Redis PubSub, and Opus audio transcoding.',
        saas: 'Multi-tenant enterprise SaaS core with Supabase PostgreSQL Row-Level Security and pgvector semantic search.',
        zerotrust: 'Microservice service mesh with mutual TLS mTLS, Envoy API gateway ingress, and JWT RBAC authentication.',
        kafka: 'Event-driven financial transactions pipeline with Apache Kafka partition sharding and dead-letter queues DLQ.'
      };
      const prompt = archetypes[type] || archetypes.payments;
      const landingInput = document.getElementById('landingPromptInput');
      if (landingInput) landingInput.value = prompt;
      triggerGenerate(prompt);
    }

    function toggleRagIngestionDrawer() {
      const drawer = document.getElementById('ragIngestionDrawer');
      const icon = document.getElementById('ragToggleIcon');
      const label = document.getElementById('ragToggleLabel');
      if (!drawer) return;
      if (drawer.classList.contains('hidden')) {
        drawer.classList.remove('hidden');
        if (icon) icon.innerText = '▲';
        if (label) label.innerText = 'Close Ingestion Drawer';
      } else {
        drawer.classList.add('hidden');
        if (icon) icon.innerText = '▼';
        if (label) label.innerText = '+ Ingest Custom Specs / Files';
      }
    }

    """
    if "function triggerGenerate" not in content:
        content = content.replace(js_needle, new_js + js_needle)

    # 7. Update confirmCouncilRun to simply call triggerGenerate()
    confirm_old = """function confirmCouncilRun() {
      toggleCouncilModal();
      if (!lastTranscript) {
        showToast('Speak via the microphone pill or upload audio to convene.');
        switchView('landing');
      } else {
        runCouncilDeliberation(lastTranscript);
      }
    }"""
    confirm_new = """function confirmCouncilRun() {
      triggerGenerate();
    }"""
    if confirm_old in content:
        content = content.replace(confirm_old, confirm_new)

    with open('web_app/index.html', 'w', encoding='utf-8') as f:
        f.write(content)
    
    # Also sync to frontend_demo.html
    with open('frontend_demo.html', 'w', encoding='utf-8') as f:
        f.write(content)

    print("Successfully updated web_app/index.html and frontend_demo.html with de-cramped spacious layout and immediate Council convening!")

if __name__ == '__main__':
    update_index_html()
