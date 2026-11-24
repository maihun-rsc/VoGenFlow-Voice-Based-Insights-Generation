"""
Export Service Module
Writes generated markdown specifications into target repositories or project directories.
"""

import datetime
import os
from pathlib import Path
from typing import Dict, List, Optional


class ExportService:
    """Handles saving generated blueprint files to local filesystem destinations and Word .docx documents."""

    @staticmethod
    def export_documents(documents: Dict[str, str], target_dir: str) -> List[str]:
        """Save a dictionary of {filename: content} into the target directory."""
        dest_path = Path(target_dir)
        dest_path.mkdir(parents=True, exist_ok=True)

        saved_files = []
        for filename, content in documents.items():
            if not content.strip():
                continue
            file_path = dest_path / filename
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            saved_files.append(str(file_path))

        return saved_files

    @staticmethod
    def save_single_document(filename: str, content: str, target_dir: str) -> str:
        """Save a single document."""
        dest_path = Path(target_dir)
        dest_path.mkdir(parents=True, exist_ok=True)
        file_path = dest_path / filename
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        return str(file_path)

    @staticmethod
    def export_to_docx(
        documents: Dict[str, str],
        output_path: str,
        project_name: str = "VoGenFlow Industrial Specification",
        preset_name: str = "Standard Monolith Council (6-Seat)"
    ) -> str:
        """Bundle the 5 core specifications into a professional, clean .docx document using python-docx."""
        try:
            import docx
            from docx.shared import Inches, Pt, RGBColor
            from docx.enum.text import WD_ALIGN_PARAGRAPH
            from docx.enum.table import WD_TABLE_ALIGNMENT
            from docx.oxml import OxmlElement, parse_xml
            from docx.oxml.ns import nsdecls, qn
        except ImportError:
            raise ImportError("python-docx is required for Word document export. Install via: pip install python-docx")

        doc = docx.Document()

        # Set page margins (1 inch)
        for section in doc.sections:
            section.top_margin = Inches(1.0)
            section.bottom_margin = Inches(1.0)
            section.left_margin = Inches(1.0)
            section.right_margin = Inches(1.0)

        # Style definition helper
        gold_color = RGBColor(184, 134, 11)   # #B8860B
        dark_color = RGBColor(15, 23, 42)     # #0F172A
        muted_color = RGBColor(100, 116, 139) # #64748B

        # Document Title / Cover Header
        title_p = doc.add_paragraph()
        title_p.paragraph_format.space_before = Pt(0)
        title_p.paragraph_format.space_after = Pt(4)
        run_title = title_p.add_run("VOGENFLOW INDUSTRIAL SPECIFICATION")
        run_title.font.name = "Calibri"
        run_title.font.size = Pt(22)
        run_title.font.bold = True
        run_title.font.color.rgb = dark_color

        # Subtitle / Project Name
        sub_p = doc.add_paragraph()
        sub_p.paragraph_format.space_after = Pt(12)
        run_sub = sub_p.add_run(project_name)
        run_sub.font.name = "Calibri"
        run_sub.font.size = Pt(14)
        run_sub.font.color.rgb = gold_color
        run_sub.font.bold = True

        # Metadata table
        meta_table = doc.add_table(rows=3, cols=2)
        meta_table.alignment = WD_TABLE_ALIGNMENT.LEFT
        meta_table.autofit = True
        meta_data = [
            ("Authoring Body", "VoGenFlow Autonomous Architecture Council (6-Seat)"),
            ("Council Preset", preset_name),
            ("Generated Date", datetime.datetime.now().strftime("%B %d, %Y - %H:%M:%S UTC")),
        ]
        for row_idx, (k, v) in enumerate(meta_data):
            c0 = meta_table.cell(row_idx, 0)
            c1 = meta_table.cell(row_idx, 1)
            c0.text = k
            c1.text = v
            c0.paragraphs[0].runs[0].font.bold = True
            c0.paragraphs[0].runs[0].font.color.rgb = muted_color
            c0.paragraphs[0].runs[0].font.size = Pt(9.5)
            c1.paragraphs[0].runs[0].font.color.rgb = dark_color
            c1.paragraphs[0].runs[0].font.size = Pt(9.5)

        doc.add_paragraph().paragraph_format.space_after = Pt(16)

        # Standard specification section ordering
        spec_keys = [
            ("PRD.md", "1. Product Requirements Document (PRD)"),
            ("Architecture.md", "2. System Architecture & PostgreSQL DDL"),
            ("Flow.md", "3. Lifecycle Sequence Flows & Operational Recovery"),
            ("tasks.md", "4. Phased Engineering Tasks & Verification Plan"),
            ("design.md", "5. Monolith Luxury UI/UX Design System"),
            ("master_execution_bundle.md", "6. Master Execution Bundle & Contracts"),
        ]

        # Case-insensitive map of provided documents
        doc_map = {}
        for k, v in documents.items():
            doc_map[k.lower()] = (k, v)
            base_k = os.path.basename(k).lower()
            doc_map[base_k] = (k, v)

        # Map design_proposal.md to design.md if present
        if "design_proposal.md" in doc_map and "design.md" not in doc_map:
            doc_map["design.md"] = doc_map["design_proposal.md"]

        first_section = True
        for key, display_title in spec_keys:
            key_lower = key.lower()
            if key_lower not in doc_map:
                continue

            orig_name, text = doc_map[key_lower]
            if not text or not text.strip():
                continue

            if not first_section:
                doc.add_page_break()
            first_section = False

            # Section Header (Heading 1)
            h1 = doc.add_paragraph()
            h1.paragraph_format.space_before = Pt(14)
            h1.paragraph_format.space_after = Pt(8)
            h1.paragraph_format.keep_with_next = True
            r_h1 = h1.add_run(display_title)
            r_h1.font.name = "Calibri"
            r_h1.font.size = Pt(16)
            r_h1.font.bold = True
            r_h1.font.color.rgb = dark_color

            # Parse lines of Markdown
            in_code_block = False
            code_buffer = []

            lines = text.split("\n")
            line_idx = 0
            while line_idx < len(lines):
                line = lines[line_idx]
                stripped = line.strip()

                if stripped.startswith("```"):
                    if in_code_block:
                        # End code block
                        in_code_block = False
                        code_text = "\n".join(code_buffer)
                        code_p = doc.add_paragraph()
                        code_p.paragraph_format.space_before = Pt(4)
                        code_p.paragraph_format.space_after = Pt(6)
                        code_p.paragraph_format.left_indent = Inches(0.2)
                        run_code = code_p.add_run(code_text)
                        run_code.font.name = "Consolas"
                        run_code.font.size = Pt(8.5)
                        run_code.font.color.rgb = RGBColor(30, 41, 59)
                        code_buffer.clear()
                    else:
                        in_code_block = True
                        code_buffer.clear()
                    line_idx += 1
                    continue

                if in_code_block:
                    code_buffer.append(line)
                    line_idx += 1
                    continue

                # Markdown table detection
                if stripped.startswith("|") and stripped.endswith("|") and line_idx + 1 < len(lines) and "|---" in lines[line_idx + 1]:
                    table_lines = [stripped]
                    line_idx += 1
                    table_lines.append(lines[line_idx].strip()) # separator line
                    line_idx += 1
                    while line_idx < len(lines) and lines[line_idx].strip().startswith("|") and lines[line_idx].strip().endswith("|"):
                        table_lines.append(lines[line_idx].strip())
                        line_idx += 1

                    # Process table
                    parsed_rows = []
                    for t_line in table_lines:
                        if "|---" in t_line or "|:--" in t_line:
                            continue
                        cells = [c.strip() for c in t_line.split("|")[1:-1]]
                        if cells:
                            parsed_rows.append(cells)

                    if parsed_rows:
                        num_cols = max(len(r) for r in parsed_rows)
                        w_table = doc.add_table(rows=len(parsed_rows), cols=num_cols)
                        w_table.style = 'Table Grid'
                        w_table.alignment = WD_TABLE_ALIGNMENT.LEFT
                        for r_i, row_cells in enumerate(parsed_rows):
                            for c_i, cell_text in enumerate(row_cells):
                                if c_i < num_cols:
                                    w_cell = w_table.cell(r_i, c_i)
                                    w_cell.text = cell_text
                                    p = w_cell.paragraphs[0]
                                    if p.runs:
                                        p.runs[0].font.size = Pt(9.0)
                                        if r_i == 0:
                                            p.runs[0].font.bold = True
                                            p.runs[0].font.color.rgb = dark_color
                    continue

                if not stripped:
                    line_idx += 1
                    continue

                # Headings
                if stripped.startswith("# "):
                    h = doc.add_paragraph()
                    h.paragraph_format.space_before = Pt(12)
                    h.paragraph_format.space_after = Pt(4)
                    h.paragraph_format.keep_with_next = True
                    r = h.add_run(stripped[2:])
                    r.font.size = Pt(14)
                    r.font.bold = True
                    r.font.color.rgb = dark_color
                elif stripped.startswith("## "):
                    h = doc.add_paragraph()
                    h.paragraph_format.space_before = Pt(10)
                    h.paragraph_format.space_after = Pt(3)
                    h.paragraph_format.keep_with_next = True
                    r = h.add_run(stripped[3:])
                    r.font.size = Pt(12)
                    r.font.bold = True
                    r.font.color.rgb = gold_color
                elif stripped.startswith("### "):
                    h = doc.add_paragraph()
                    h.paragraph_format.space_before = Pt(8)
                    h.paragraph_format.space_after = Pt(2)
                    h.paragraph_format.keep_with_next = True
                    r = h.add_run(stripped[4:])
                    r.font.size = Pt(10.5)
                    r.font.bold = True
                    r.font.color.rgb = dark_color
                elif stripped.startswith("- ") or stripped.startswith("* ") or stripped.startswith("- [ ]") or stripped.startswith("- [x]"):
                    bp = doc.add_paragraph(style='List Bullet')
                    bp.paragraph_format.space_before = Pt(1)
                    bp.paragraph_format.space_after = Pt(2)
                    bullet_text = stripped
                    for prefix in ["- [ ] ", "- [x] ", "- ", "* "]:
                        if bullet_text.startswith(prefix):
                            bullet_text = bullet_text[len(prefix):]
                            break
                    r = bp.add_run(bullet_text)
                    r.font.size = Pt(10)
                else:
                    p = doc.add_paragraph()
                    p.paragraph_format.space_before = Pt(2)
                    p.paragraph_format.space_after = Pt(3)
                    r = p.add_run(stripped)
                    r.font.size = Pt(10)

                line_idx += 1

        # If any lingering code buffer
        if code_buffer:
            code_text = "\n".join(code_buffer)
            code_p = doc.add_paragraph()
            run_code = code_p.add_run(code_text)
            run_code.font.name = "Consolas"
            run_code.font.size = Pt(8.5)

        out_path = Path(output_path).resolve()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        doc.save(str(out_path))
        return str(out_path)
