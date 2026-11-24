"""Patch Vo-Gen-Flow web_app/index.html to add live Council Chamber thinking and Sample Audio Note loading."""
import sys
import re

html_path = 'E:/voice-insight-generation/web_app/index.html'
with open(html_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update dropzone to include Sample Audio Quick-Test Controls
drop_target = '''        <div>
          <h3 class="text-sm md:text-base font-semibold" style="color: var(--text-main);">Drop Technical Audio Note or Click to Browse</h3>
          <p class="text-xs font-light mt-1" style="color: var(--text-muted);">
            Supports .WAV, .MP3, .M4A, .OGG, .WEBM up to 25MB. Automatically transcribes and convenes the Council.
          </p>
        </div>'''

drop_replacement = '''        <div>
          <h3 class="text-sm md:text-base font-semibold" style="color: var(--text-main);">Drop Technical Audio Note or Click to Browse</h3>
          <p class="text-xs font-light mt-1" style="color: var(--text-muted);">
            Supports .WAV, .MP3, .M4A, .OGG, .WEBM up to 25MB. Automatically transcribes and convenes the Council.
          </p>
        </div>

        <!-- Sample Audio Quick-Test Controls -->
        <div class="pt-2 flex flex-wrap items-center justify-center gap-2">
          <button 
            type="button"
            onclick="loadSampleAudioNote(event)" 
            class="px-3.5 py-1.5 rounded-xl text-xs font-mono-telemetry font-semibold border transition-all flex items-center space-x-2 shadow-sm hover:scale-[1.02] active:scale-95" 
            style="background: rgba(212, 175, 55, 0.15); border-color: var(--accent-gold); color: var(--accent-gold);"
            title="Load and transcribe pre-recorded financial architecture audio"
          >
            <span>🎙️ LOAD SAMPLE ARCHITECTURE AUDIO NOTE (WAV)</span>
            <span>✦</span>
          </button>
          <a 
            href="/api/stt/sample-audio" 
            download="sample_architecture_audio.wav"
            onclick="event.stopPropagation()"
            class="px-2.5 py-1.5 rounded-xl text-[10px] font-mono-telemetry border transition-all hover:text-white"
            style="border-color: var(--card-border); color: var(--text-muted);"
            title="Download WAV to test drag-and-drop file upload"
          >
            ↓ DOWNLOAD WAV
          </a>
        </div>'''

if drop_target in content:
    content = content.replace(drop_target, drop_replacement, 1)
    print("1. Dropzone updated successfully.")
else:
    print("1. Warning: dropzone target not found!")

# 2. Update seat inspector card in the modal
inspector_target = '''      <!-- Dedicated Interactive Seat Inspector Dossier -->
      <div id="seatInspectorCard" class="p-3 sm:p-4 rounded-2xl border transition-all shrink-0" style="background: var(--card-bg); border-color: var(--card-border);">
        <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-2.5">
          <div class="space-y-1">
            <div class="flex items-center space-x-2">
              <span id="seatInspectorBadge" class="px-2 py-0.5 rounded-full text-[9px] font-mono-telemetry font-bold bg-emerald-500/15 text-emerald-400 border border-emerald-500/30">SEAT: STRATEGIST</span>
              <span id="seatInspectorModel" class="text-[9px] font-mono-telemetry" style="color: var(--text-subtle);">// QWEN 27B / GROQ LPU</span>
            </div>
            <div id="seatInspectorTitle" class="text-xs sm:text-sm font-semibold" style="color: var(--text-main);">Principal PM — Strategic PRD &amp; Personas</div>
            <div id="seatInspectorDesc" class="text-[11px] font-light leading-relaxed line-clamp-2" style="color: var(--text-muted);">Synthesizes product requirements, user personas, non-functional SLAs, and STRIDE security boundaries.</div>
          </div>
          <div class="shrink-0">
            <span id="seatInspectorStage" class="px-2.5 py-0.5 rounded-full text-[9px] font-mono-telemetry border border-emerald-500/30 text-emerald-400 bg-emerald-500/10 font-semibold">DAG STAGE 1</span>
          </div>
        </div>
      </div>'''

inspector_replacement = '''      <!-- Dedicated Interactive Seat Inspector Dossier -->
      <div id="seatInspectorCard" class="p-3 sm:p-4 rounded-2xl border transition-all shrink-0 space-y-2.5" style="background: var(--card-bg); border-color: var(--card-border);">
        <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-2.5">
          <div class="space-y-1">
            <div class="flex items-center space-x-2">
              <span id="seatInspectorBadge" class="px-2 py-0.5 rounded-full text-[9px] font-mono-telemetry font-bold bg-emerald-500/15 text-emerald-400 border border-emerald-500/30">SEAT: STRATEGIST</span>
              <span id="seatInspectorModel" class="text-[9px] font-mono-telemetry" style="color: var(--text-subtle);">// OPENAI/GPT-OSS-120B // GROQ LPU</span>
            </div>
            <div id="seatInspectorTitle" class="text-xs sm:text-sm font-semibold" style="color: var(--text-main);">Strategist — Principal Technical PM</div>
            <div id="seatInspectorDesc" class="text-[11px] font-light leading-relaxed" style="color: var(--text-muted);">Synthesizes strategic PRD, user personas, non-functional SLAs, and STRIDE security boundaries.</div>
          </div>
          <div class="flex items-center space-x-2 shrink-0">
            <span id="seatInspectorStage" class="px-2.5 py-0.5 rounded-full text-[9px] font-mono-telemetry border border-emerald-500/30 text-emerald-400 bg-emerald-500/10 font-semibold">DAG STAGE 1</span>
            <button id="seatInspectorArtifactBtn" onclick="viewSeatArtifact('PRD.md')" class="px-2.5 py-1 rounded-xl text-[10px] font-mono-telemetry font-semibold border flex items-center space-x-1 transition-all hover:opacity-90" style="border-color: var(--accent-gold); color: var(--accent-gold); background: rgba(212,175,55,0.1);">
              <span>VIEW PRD</span>
              <span>✦</span>
            </button>
          </div>
        </div>

        <!-- Real-Time Agent Thinking & Deliberation Flow -->
        <div id="seatInspectorThoughtsBox" class="p-2.5 rounded-xl border text-[11px] font-mono-telemetry leading-relaxed flex items-start space-x-2" style="background: var(--input-bg); border-color: var(--card-border);">
          <span class="text-amber-400 shrink-0 mt-0.5">💭</span>
          <div class="w-full">
            <div class="text-[9px] uppercase tracking-wider font-bold text-amber-400">AGENT DELIBERATION RATIONALE &amp; THOUGHTS</div>
            <div id="seatInspectorThoughts" class="mt-0.5 text-neutral-300 italic" style="color: var(--text-main);">
              Ready to deliberate. Convenes upon voice capture or prompt submission to synthesize target architecture.
            </div>
          </div>
        </div>
      </div>'''

if inspector_target in content:
    content = content.replace(inspector_target, inspector_replacement, 1)
    print("2. Inspector card updated successfully.")
else:
    print("2. Warning: inspector target not found!")

# 3. Update selectSeat, runCouncilDeliberation, and add loadSampleAudioNote + viewSeatArtifact
js_target = '''    function selectSeat(name, model, role, desc, stage) {
      const badge = document.getElementById('seatInspectorBadge');
      const modelEl = document.getElementById('seatInspectorModel');
      const titleEl = document.getElementById('seatInspectorTitle');
      const descEl = document.getElementById('seatInspectorDesc');
      const stageEl = document.getElementById('seatInspectorStage');
      
      if (badge) badge.innerText = `SEAT: ${name.toUpperCase()}`;
      if (modelEl) modelEl.innerText = `// ${model}`;
      if (titleEl) titleEl.innerText = `${role} — ${name}`;
      if (descEl) descEl.innerText = desc || 'Specialist council agent executing deterministic step in DAG.';
      if (stageEl) stageEl.innerText = stage || 'ACTIVE AGENT';
      
      showToast(`Selected Seat: ${name} (${role})`);
    }'''

js_replacement = '''    let latestSeatDossier = {};

    function selectSeat(name, model, role, desc, stage) {
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
          else if (cleanKey === 'curator') art = 'Architecture.md';
          else if (cleanKey === 'elder') art = 'tasks.md';
          artifactBtn.onclick = () => viewSeatArtifact(art);
          artifactBtn.innerHTML = `<span>VIEW ${art}</span><span>✦</span>`;
        }
      }
      
      showToast(`Selected Seat: ${name} (${role || 'Agent'})`);
    }

    function viewSeatArtifact(key) {
      if (isCouncilOpen) toggleCouncilModal();
      switchView('specs');
      if (key === 'PRD.md') switchDocTab('prd');
      else if (key === 'Architecture.md') switchDocTab('arch');
      else if (key === 'Flow.md') switchDocTab('flow');
      else if (key === 'tasks.md') switchDocTab('tasks');
    }

    async function loadSampleAudioNote(event) {
      if (event) event.stopPropagation();
      showToast('Loading pre-recorded financial architecture audio note...');
      addLogEntry('Fetching sample audio (data/sample_audio.wav)...');
      try {
        const res = await fetch(`${API_BASE}/api/stt/sample-audio`);
        if (!res.ok) throw new Error('Could not fetch sample audio.');
        const blob = await res.blob();
        showToast('Ingesting & transcribing sample audio note...');
        await processAudioBlob(blob, 'sample_financial_architecture.wav');
      } catch (err) {
        console.warn('Sample audio fetch failed, using fallback transcript:', err);
        const sampleText = "We need to architect a high-throughput event-driven financial transactions pipeline. It must process payment events using Apache Kafka, store ledger records in PostgreSQL with row-level security, provide sub-millisecond fraud checks via Redis cache-aside, and expose an async fast API gateway.";
        triggerGenerate(sampleText);
      }
    }'''

if js_target in content:
    content = content.replace(js_target, js_replacement, 1)
    print("3. selectSeat and helper functions updated successfully.")
else:
    print("3. Warning: selectSeat target not found!")

# 4. In runCouncilDeliberation, store seat_dossier
dossier_target = '''        const data = await res.json();
        activeSessionId = data.session_id;'''

dossier_replacement = '''        const data = await res.json();
        activeSessionId = data.session_id;
        if (data.seat_dossier) {
          latestSeatDossier = data.seat_dossier;
          const statusText = document.getElementById('councilStatusText');
          if (statusText) statusText.innerText = `CONSENSUS REACHED (${data.duration_seconds}s)`;
          selectSeat('Strategist');
        }'''

if dossier_target in content:
    content = content.replace(dossier_target, dossier_replacement, 1)
    print("4. runCouncilDeliberation updated to store seat_dossier.")
else:
    print("4. Warning: dossier_target not found!")

with open(html_path, 'w', encoding='utf-8') as f:
    f.write(content)
print("Complete! index.html patched successfully.")
