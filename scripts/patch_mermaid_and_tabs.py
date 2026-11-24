"""
Patch web_app/index.html to add:
1. Mermaid.js CDN integration for rendering C4 & Sequence diagrams visually
2. 6-tab Specification Studio: PRD.md, architecture.md, flow.md, tasks.md, design.md, bundle.md
3. Live Mermaid re-render on tab switch and theme toggle
Mirrors updates to frontend_demo.html.
"""

from pathlib import Path
import re

INDEX_PATH = Path(r"E:\voice-insight-generation\web_app\index.html")
DEMO_PATH = Path(r"E:\voice-insight-generation\frontend_demo.html")

content = INDEX_PATH.read_text(encoding="utf-8")

# 1. Add Mermaid.js to <head>
if "mermaid.min.js" not in content:
    content = content.replace(
        '<script src="https://www.gstatic.com/antigravity/web/dev/tailwindcss.min.js"></script>',
        '<script src="https://www.gstatic.com/antigravity/web/dev/tailwindcss.min.js"></script>\n  <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>'
    )
    print("Added Mermaid CDN script to <head>")

# 2. Add design.md and bundle.md buttons to doc tabs bar
old_tabs_bar = """        <div class="flex items-center space-x-2 p-1.5 rounded-xl border text-xs font-mono-telemetry" style="background: var(--card-bg); border-color: var(--card-border);">
          <button id="doc-prd" onclick="switchDocTab('prd')" class="px-4 py-2 rounded-lg font-medium" style="background: var(--input-bg); color: var(--text-main);">PRD.md</button>
          <button id="doc-arch" onclick="switchDocTab('arch')" class="px-4 py-2 rounded-lg hover:opacity-100" style="color: var(--text-muted);">architecture.md</button>
          <button id="doc-flow" onclick="switchDocTab('flow')" class="px-4 py-2 rounded-lg hover:opacity-100" style="color: var(--text-muted);">flow.md</button>
          <button id="doc-tasks" onclick="switchDocTab('tasks')" class="px-4 py-2 rounded-lg hover:opacity-100" style="color: var(--text-muted);">tasks.md</button>
        </div>"""

new_tabs_bar = """        <div class="flex items-center space-x-2 p-1.5 rounded-xl border text-xs font-mono-telemetry overflow-x-auto" style="background: var(--card-bg); border-color: var(--card-border);">
          <button id="doc-prd" onclick="switchDocTab('prd')" class="px-3.5 py-2 rounded-lg font-medium whitespace-nowrap" style="background: var(--input-bg); color: var(--text-main);">PRD.md</button>
          <button id="doc-arch" onclick="switchDocTab('arch')" class="px-3.5 py-2 rounded-lg hover:opacity-100 whitespace-nowrap" style="color: var(--text-muted);">architecture.md</button>
          <button id="doc-flow" onclick="switchDocTab('flow')" class="px-3.5 py-2 rounded-lg hover:opacity-100 whitespace-nowrap" style="color: var(--text-muted);">flow.md</button>
          <button id="doc-tasks" onclick="switchDocTab('tasks')" class="px-3.5 py-2 rounded-lg hover:opacity-100 whitespace-nowrap" style="color: var(--text-muted);">tasks.md</button>
          <button id="doc-design" onclick="switchDocTab('design')" class="px-3.5 py-2 rounded-lg hover:opacity-100 whitespace-nowrap" style="color: var(--text-muted);">design.md</button>
          <button id="doc-bundle" onclick="switchDocTab('bundle')" class="px-3.5 py-2 rounded-lg hover:opacity-100 whitespace-nowrap" style="color: var(--text-muted);">bundle.md</button>
        </div>"""

if old_tabs_bar in content:
    content = content.replace(old_tabs_bar, new_tabs_bar)
    print("Added design.md and bundle.md buttons to tabs bar")

# 3. Update docData in script
old_doc_data = """    const docData = {
      prd: null,
      arch: null,
      flow: null,
      tasks: null
    };"""

new_doc_data = """    const docData = {
      prd: null,
      arch: null,
      flow: null,
      tasks: null,
      design: null,
      bundle: null
    };"""

if old_doc_data in content:
    content = content.replace(old_doc_data, new_doc_data)
    print("Updated docData object with design and bundle keys")

# 4. Update switchDocTab
old_switch_tab = """    function switchDocTab(tabName) {
      currentDocTab = tabName;
      ['prd', 'arch', 'flow', 'tasks'].forEach(t => {"""

new_switch_tab = """    function switchDocTab(tabName) {
      currentDocTab = tabName;
      ['prd', 'arch', 'flow', 'tasks', 'design', 'bundle'].forEach(t => {"""

if old_switch_tab in content:
    content = content.replace(old_switch_tab, new_switch_tab)
    print("Updated switchDocTab to cover all 6 tabs")

# 5. Update renderCurrentDocTab to call mermaid.run
old_render_tab = """      } else {
        container.innerHTML = docData[currentDocTab];
      }
    }"""

new_render_tab = """      } else {
        container.innerHTML = docData[currentDocTab];
        if (window.mermaid) {
          try {
            mermaid.run({ nodes: container.querySelectorAll('.mermaid') });
          } catch(merr) {
            console.warn("Mermaid rendering warning:", merr);
          }
        }
      }
    }"""

if old_render_tab in content:
    content = content.replace(old_render_tab, new_render_tab)
    print("Added mermaid.run call inside renderCurrentDocTab")

# 6. Update formatMarkdown to render .mermaid class
old_code_replace = """      // Code blocks ```lang ... ```
      html = html.replace(/```([a-zA-Z0-9_\\-\\.]*)\\n([\\s\\S]*?)```/g, (match, lang, code) => {
        return `<div class="my-5 rounded-xl border overflow-hidden" style="border-color: var(--card-border); background: var(--code-bg);">
          <div class="px-4 py-2 border-b flex items-center justify-between text-[10px] font-mono-telemetry" style="border-color: var(--card-border); background: var(--bezel-bg); color: var(--text-muted);">
            <span class="uppercase font-semibold tracking-wider" style="color: var(--accent-gold);">${lang || 'CODE'}</span>
            <button onclick="navigator.clipboard.writeText(this.parentElement.nextElementSibling.innerText); showToast('Code copied to clipboard');" class="hover:opacity-100 transition-opacity font-bold">COPY</button>
          </div>
          <pre class="p-4 md:p-5 overflow-x-auto text-xs font-mono-telemetry leading-relaxed" style="color: var(--code-text);"><code>${code.trim()}</code></pre>
        </div>`;
      });"""

new_code_replace = """      // Code blocks ```lang ... ```
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
      });"""

if old_code_replace in content:
    content = content.replace(old_code_replace, new_code_replace)
    print("Enhanced formatMarkdown with visual Mermaid diagram container")

# 7. Update viewSeatArtifact to handle all 6 artifacts
old_view_artifact = """    function viewSeatArtifact(key) {
      if (isCouncilOpen) toggleCouncilModal();
      switchView('specs');
      if (key === 'PRD.md') switchDocTab('prd');
      else if (key === 'Architecture.md') switchDocTab('arch');
      else if (key === 'Flow.md') switchDocTab('flow');
      else if (key === 'tasks.md') switchDocTab('tasks');
    }"""

new_view_artifact = """    function viewSeatArtifact(key) {
      if (isCouncilOpen) toggleCouncilModal();
      switchView('specs');
      if (key === 'PRD.md') switchDocTab('prd');
      else if (key === 'Architecture.md') switchDocTab('arch');
      else if (key === 'Flow.md') switchDocTab('flow');
      else if (key === 'tasks.md') switchDocTab('tasks');
      else if (key === 'design_proposal.md') switchDocTab('design');
      else if (key === 'master_execution_bundle.md') switchDocTab('bundle');
    }"""

if old_view_artifact in content:
    content = content.replace(old_view_artifact, new_view_artifact)
    print("Updated viewSeatArtifact mapping")

# 8. Populate artifacts for design and bundle in runCouncilDeliberation & restore
old_pop = """        if (data.artifacts) {
          if (data.artifacts["PRD.md"]) docData.prd = formatMarkdown(data.artifacts["PRD.md"]);
          if (data.artifacts["Architecture.md"]) docData.arch = formatMarkdown(data.artifacts["Architecture.md"]);
          if (data.artifacts["Flow.md"]) docData.flow = formatMarkdown(data.artifacts["Flow.md"]);
          if (data.artifacts["tasks.md"]) docData.tasks = formatMarkdown(data.artifacts["tasks.md"]);
          switchDocTab('prd');
        }"""

new_pop = """        if (data.artifacts) {
          if (data.artifacts["PRD.md"]) docData.prd = formatMarkdown(data.artifacts["PRD.md"]);
          if (data.artifacts["Architecture.md"]) docData.arch = formatMarkdown(data.artifacts["Architecture.md"]);
          if (data.artifacts["Flow.md"]) docData.flow = formatMarkdown(data.artifacts["Flow.md"]);
          if (data.artifacts["tasks.md"]) docData.tasks = formatMarkdown(data.artifacts["tasks.md"]);
          if (data.artifacts["design_proposal.md"]) docData.design = formatMarkdown(data.artifacts["design_proposal.md"]);
          if (data.artifacts["master_execution_bundle.md"]) docData.bundle = formatMarkdown(data.artifacts["master_execution_bundle.md"]);
          switchDocTab('prd');
        }"""

if old_pop in content:
    content = content.replace(old_pop, new_pop)
    print("Populated docData with design and bundle from deliberation response")

# 9. Initialize Mermaid in window.onload
if "mermaid.initialize" not in content:
    content = content.replace(
        "window.addEventListener('DOMContentLoaded', () => {",
        "window.addEventListener('DOMContentLoaded', () => {\n      if (window.mermaid) { mermaid.initialize({ startOnLoad: false, theme: 'dark' }); }"
    )
    print("Initialized Mermaid in DOMContentLoaded")

# Write out changes
INDEX_PATH.write_text(content, encoding="utf-8")
DEMO_PATH.write_text(content, encoding="utf-8")
print(f"Patched {INDEX_PATH} and mirrored to {DEMO_PATH}")
