from pathlib import Path

def patch_html_file(file_path: Path):
    content = file_path.read_text(encoding="utf-8")
    
    # 1. Add docx.js to head if not present
    if "docx@8.5.0" not in content:
        mermaid_script = '<script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>'
        docx_script = mermaid_script + '\n  <script src="https://unpkg.com/docx@8.5.0/build/index.js"></script>'
        if mermaid_script in content:
            content = content.replace(mermaid_script, docx_script)
            print(f"Added docx.js to {file_path.name}")

    # 2. Add DOWNLOAD .DOCX button in View 3 header if not present
    if "exportToDocx()" not in content:
        git_btn = """          <button onclick="exportGitScript()" class="flex-1 sm:flex-initial px-4 sm:px-5 py-2 sm:py-2.5 rounded-xl text-xs font-mono-telemetry font-bold transition-all shadow-md text-center" style="background: var(--accent-gold); color: #000;">
            EXPORT GIT SCRIPT
          </button>"""
        
        new_btns = git_btn + """\n          <button onclick="exportToDocx()" class="flex-1 sm:flex-initial px-4 sm:px-5 py-2 sm:py-2.5 rounded-xl text-xs font-mono-telemetry font-bold transition-all shadow-md text-center hover:opacity-90" style="background: #2563eb; color: #fff;">
            DOWNLOAD .DOCX
          </button>"""
        if git_btn in content:
            content = content.replace(git_btn, new_btns)
            print(f"Added DOWNLOAD .DOCX button to {file_path.name}")

    # 3. Add rawArtifacts, currentProjectIR, and exportToDocx function
    if "function exportToDocx(" not in content:
        export_func = """
    let rawArtifacts = {};
    let currentProjectIR = null;

    async function exportToDocx() {
      if (!window.docx) {
        showToast('Loading Word document generator...');
        try {
          await new Promise((resolve, reject) => {
            const s = document.createElement('script');
            s.src = 'https://unpkg.com/docx@8.5.0/build/index.js';
            s.onload = resolve;
            s.onerror = () => reject(new Error('Failed to load docx.js'));
            document.head.appendChild(s);
          });
        } catch (e) {
          alert('Could not load docx.js: ' + e.message);
          return;
        }
      }

      const { Document, Packer, Paragraph, TextRun, HeadingLevel } = window.docx;
      
      const prdRaw = rawArtifacts?.["PRD.md"] || "";
      const archRaw = rawArtifacts?.["Architecture.md"] || "";
      const flowRaw = rawArtifacts?.["Flow.md"] || "";
      const tasksRaw = rawArtifacts?.["tasks.md"] || "";
      const designRaw = rawArtifacts?.["design_proposal.md"] || "";
      
      const projectName = document.getElementById('sidebarProjectTitle')?.innerText || 'VoGenFlow Project';
      
      const docChildren = [
        new Paragraph({
          text: "VoGenFlow Engineering Specification",
          heading: HeadingLevel.TITLE,
          spacing: { after: 200 }
        }),
        new Paragraph({
          children: [
            new TextRun({ text: "Project: ", bold: true }),
            new TextRun({ text: projectName }),
          ],
          spacing: { after: 120 }
        }),
        new Paragraph({
          children: [
            new TextRun({ text: "Generated: ", bold: true }),
            new TextRun({ text: new Date().toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' }) }),
            new TextRun({ text: " | Author: ", bold: true }),
            new TextRun({ text: "VoGenFlow Autonomous Architecture Council" }),
          ],
          spacing: { after: 400 }
        })
      ];

      function addSectionContent(sectionTitle, text) {
        if (!text) return;
        docChildren.push(new Paragraph({
          text: sectionTitle,
          heading: HeadingLevel.HEADING_1,
          spacing: { before: 300, after: 150 }
        }));
        const lines = text.split('\\n');
        for (const line of lines) {
          const trimmed = line.trim();
          if (!trimmed) continue;
          if (trimmed.startsWith('# ')) {
            docChildren.push(new Paragraph({ text: trimmed.replace(/^#\\s+/, ''), heading: HeadingLevel.HEADING_2, spacing: { before: 200, after: 80 } }));
          } else if (trimmed.startsWith('## ')) {
            docChildren.push(new Paragraph({ text: trimmed.replace(/^##\\s+/, ''), heading: HeadingLevel.HEADING_3, spacing: { before: 160, after: 60 } }));
          } else if (trimmed.startsWith('### ')) {
            docChildren.push(new Paragraph({ text: trimmed.replace(/^###\\s+/, ''), heading: HeadingLevel.HEADING_4, spacing: { before: 120, after: 40 } }));
          } else if (trimmed.startsWith('- [ ]') || trimmed.startsWith('- ') || trimmed.startsWith('* ')) {
            docChildren.push(new Paragraph({ text: trimmed.replace(/^[-*](\\s*\\[ \\])?\\s*/, '• '), spacing: { after: 40 } }));
          } else {
            docChildren.push(new Paragraph({ text: trimmed, spacing: { after: 80 } }));
          }
        }
      }

      addSectionContent("1. Executive Summary & Product Requirements (PRD)", prdRaw);
      addSectionContent("2. System Architecture & Database Models", archRaw);
      addSectionContent("3. Systems Lifecycle & Sequence Flows", flowRaw);
      addSectionContent("4. Phased Implementation Tasks & Verification Plan", tasksRaw);
      if (designRaw) {
        addSectionContent("5. UI/UX Design System Specifications", designRaw);
      }

      const doc = new Document({
        sections: [{
          properties: {},
          children: docChildren
        }]
      });

      showToast('Generating Word (.docx) document...');
      Packer.toBlob(doc).then(blob => {
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        const cleanFile = projectName.toLowerCase().replace(/[^a-z0-9_-]/g, '_');
        a.download = `${cleanFile}_specification.docx`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        showToast('✓ .docx downloaded successfully!');
      }).catch(err => {
        console.error('Docx generation error:', err);
        alert('Failed to generate .docx: ' + err.message);
      });
    }
"""
        # Insert before exportGitScript function
        target = "    function exportGitScript() {"
        if target in content:
            content = content.replace(target, export_func + "\n" + target)
            print(f"Added exportToDocx function to {file_path.name}")

    # 4. In deliberate handler, save rawArtifacts and currentProjectIR
    delib_target = "if (data.artifacts) {"
    delib_replacement = """if (data.artifacts) {
          rawArtifacts = data.artifacts;
          currentProjectIR = data.project_ir || null;"""
    if delib_target in content and "rawArtifacts = data.artifacts;" not in content:
        content = content.replace(delib_target, delib_replacement, 1)
        print(f"Wired rawArtifacts in deliberate callback for {file_path.name}")

    file_path.write_text(content, encoding="utf-8")

patch_html_file(Path("E:/voice-insight-generation/web_app/index.html"))
patch_html_file(Path("E:/voice-insight-generation/frontend_demo.html"))
print("Done patching HTML files.")
