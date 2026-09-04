"""Autonomous Multi-Model Council Orchestration Engine for Vo-Gen-Flow."""

import os
import json
import time
import logging
from typing import Dict, Any, Optional, List, Callable
from pathlib import Path

from src.config import Config
from src.knowledge_db import CuratedKnowledgeDB
from src.model_router import ModelRouter

logger = logging.getLogger("vogenflow.council_engine")

COUNCIL_PRESETS = {
    "standard": {
        "name": "Standard Monolith Council (6-Seat)",
        "roles": ["pm_agent", "architect_agent", "ui_agent", "systems_agent", "agile_agent", "diff_agent"],
        "description": "Balanced architectural deliberation covering Strategy, C4 DDL, UI/UX, Lifecycle, and Agile plan."
    },
    "security_pentest": {
        "name": "Hardcore Security Pentest Council",
        "roles": ["pm_agent", "architect_agent", "systems_agent", "diff_agent"],
        "description": "Hardened verification focusing on STRIDE threat models, RLS policies, and zero-day attack surfaces."
    },
    "lean_sprint": {
        "name": "Lean MVP Sprint Council",
        "roles": ["pm_agent", "architect_agent", "agile_agent", "diff_agent"],
        "description": "High-velocity execution delivering minimum viable contracts and quick-start checklists."
    }
}


class CouncilEngine:
    """Coordinates the multi-model agent council DAG for voice-driven blueprint generation."""

    def __init__(
        self,
        model_router: Optional[ModelRouter] = None,
        knowledge_db: Optional[CuratedKnowledgeDB] = None,
        rag_engine: Optional[Any] = None
    ):
        self.router = model_router or ModelRouter()
        self.knowledge_db = knowledge_db or CuratedKnowledgeDB()
        self.rag_engine = rag_engine
        self.output_dir = Path(Config.OUTPUT_DIR)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def deliberate(
        self,
        transcript: str,
        preset: str = "standard",
        progress_callback: Optional[Callable[[str, Dict[str, Any]], None]] = None
    ) -> Dict[str, Any]:
        """Execute the multi-agent council DAG sequentially, piping artifacts between roles."""
        start_time = time.time()
        logger.info("Initiating Council deliberation with preset '%s'...", preset)

        if preset not in COUNCIL_PRESETS:
            logger.warning("Council preset '%s' not recognized. Falling back to 'standard'.", preset)
            preset_cfg = COUNCIL_PRESETS["standard"]
        else:
            preset_cfg = COUNCIL_PRESETS[preset]
        active_roles = preset_cfg["roles"]

        # 1. Retrieve Curated Engineering Knowledge
        knowledge_context = self.knowledge_db.format_for_prompt(transcript, top_k=2)

        # 2. Retrieve Local Codebase RAG Context if RAG engine is available
        code_context = ""
        if self.rag_engine and hasattr(self.rag_engine, "query"):
            try:
                rag_results = self.rag_engine.query(transcript, top_k=3)
                if rag_results:
                    code_context = "\n".join([f"// Context from {r.get('file', 'file')}:\n{r.get('text', '')}" for r in rag_results])
            except Exception as e:
                logger.warning("RAG retrieval skipped: %s", str(e))

        artifacts: Dict[str, str] = {}
        telemetry: List[Dict[str, Any]] = []

        def notify(role_name: str, status_msg: str, data: Optional[Dict[str, Any]] = None):
            payload = {"role": role_name, "message": status_msg, "timestamp": time.time()}
            if data:
                payload.update(data)
            logger.info("[%s] %s", role_name, status_msg)
            if progress_callback:
                try:
                    progress_callback(role_name, payload)
                except Exception as cb_err:
                    logger.warning("Progress callback failed: %s", str(cb_err))

        # --- STEP 1: Principal PM Agent (PRD) ---
        if "pm_agent" in active_roles:
            notify("pm_agent", "Principal PM deliberating on strategic PRD...")
            pm_system = (
                "You are the Principal Technical Product Manager in the Vo-Gen-Flow Council. "
                "Synthesize spoken brainstorming into an executive Product Requirements Document (PRD.md). "
                "Include: Executive Summary, Target Personas, Core Value Proposition, Functional Requirements (P0/P1), "
                "Non-Functional SLAs, and STRIDE Threat Model. Use standard Markdown."
            )
            pm_prompt = f"Spoken Transcript:\n{transcript}\n\nCurated Knowledge:\n{knowledge_context}\n\nWorkspace Context:\n{code_context}"
            pm_res = self.router.generate("pm_agent", pm_system, pm_prompt)
            artifacts["PRD.md"] = pm_res.get("content", "")
            telemetry.append(pm_res)
            notify("pm_agent", "PRD generated successfully.", {"tokens": pm_res.get("completion_tokens", 0)})

        # --- STEP 2: System Architect (Architecture & DDL) ---
        if "architect_agent" in active_roles:
            notify("architect_agent", "System Architect designing C4 container topology and PostgreSQL DDL...")
            arch_system = (
                "You are the Principal System Architect in the Vo-Gen-Flow Council. "
                "Generate architecture.md based on the PRD. "
                "Must include: Clean C4 Mermaid container diagram (`flowchart TD`), complete PostgreSQL table DDL "
                "with UUID primary keys, foreign key CASCADE rules, composite indices, and Row-Level Security policies. "
                "Ensure zero Mermaid syntax errors."
            )
            arch_prompt = f"PRD Context:\n{artifacts.get('PRD.md', transcript)}\n\nReference Architecture Snippet:\n{knowledge_context}"
            arch_res = self.router.generate("architect_agent", arch_system, arch_prompt)
            artifacts["Architecture.md"] = arch_res.get("content", "")
            telemetry.append(arch_res)
            notify("architect_agent", "Architecture and DDL synthesized.", {"tokens": arch_res.get("completion_tokens", 0)})

        # --- STEP 3: Staff UI/UX Engineer (Design Proposal) ---
        if "ui_agent" in active_roles:
            notify("ui_agent", "Staff UI/UX Engineer specifying Monolith design system & component trees...")
            ui_system = (
                "You are the Staff UI/UX Engineer in the Vo-Gen-Flow Council. "
                "Generate design_proposal.md. "
                "Specify: Monolith Luxury Reductionist design system tokens (obsidian black, midnight sapphire, hairline borders, no emojis), "
                "component hierarchy, and an interactive clickable Shadcn UI sandbox specification in JSON."
            )
            ui_prompt = f"PRD:\n{artifacts.get('PRD.md', '')}\nArchitecture:\n{artifacts.get('Architecture.md', '')}"
            ui_res = self.router.generate("ui_agent", ui_system, ui_prompt)
            artifacts["design_proposal.md"] = ui_res.get("content", "")
            telemetry.append(ui_res)
            notify("ui_agent", "UI/UX specifications completed.", {"tokens": ui_res.get("completion_tokens", 0)})

        # --- STEP 4: Systems Lifecycle Engineer (Flow & Sequences) ---
        if "systems_agent" in active_roles:
            notify("systems_agent", "Systems Lifecycle Engineer modeling sequence flows and error matrices...")
            sys_system = (
                "You are the Systems Lifecycle Engineer in the Vo-Gen-Flow Council. "
                "Generate Flow.md. "
                "Must include: Mermaid `sequenceDiagram` detailing async audio streams, WebSocket messages, "
                "state transitions (`stateDiagram-v2`), and operational failure recovery matrix."
            )
            sys_prompt = f"PRD:\n{artifacts.get('PRD.md', '')}\nArchitecture:\n{artifacts.get('Architecture.md', '')}"
            sys_res = self.router.generate("systems_agent", sys_system, sys_prompt)
            artifacts["Flow.md"] = sys_res.get("content", "")
            telemetry.append(sys_res)
            notify("systems_agent", "Lifecycle and sequence flows modeled.", {"tokens": sys_res.get("completion_tokens", 0)})

        # --- STEP 5: Agile Delivery Lead (Tasks & Plan) ---
        if "agile_agent" in active_roles:
            notify("agile_agent", "Agile Delivery Lead compiling task breakdowns and verification plan...")
            agile_system = (
                "You are the Agile Delivery Lead in the Vo-Gen-Flow Council. "
                "Generate tasks.md. "
                "Must include: Structured milestones, granular `- [ ]` checkboxes, target file paths (`[NEW]` / `[MODIFY]`), "
                "acceptance criteria, and explicit test commands."
            )
            agile_prompt = f"PRD:\n{artifacts.get('PRD.md', '')}\nArchitecture:\n{artifacts.get('Architecture.md', '')}"
            agile_res = self.router.generate("agile_agent", agile_system, agile_prompt)
            artifacts["tasks.md"] = agile_res.get("content", "")
            telemetry.append(agile_res)
            notify("agile_agent", "Agile task checklist compiled.", {"tokens": agile_res.get("completion_tokens", 0)})

        # --- STEP 6: Delta Refiner & Packager (Master Execution Bundle) ---
        if "diff_agent" in active_roles:
            notify("diff_agent", "Delta Refiner packaging zero-shot Intermediate Representation bundle...")
            diff_system = (
                "You are the Delta Refiner & Master Packager in the Vo-Gen-Flow Council. "
                "Package all council outputs into a unified master_execution_bundle.md. "
                "Provide an execution contract for downstream autonomous coding agents (Claude Code, Antigravity) "
                "with exact code blocks, target file markers, and unit test verification commands."
            )
            bundle_summary = "\n\n".join([f"### {name}\n{content[:400]}..." for name, content in artifacts.items()])
            diff_prompt = f"Council Artifacts Summary:\n{bundle_summary}\n\nSynthesize the Master Execution Bundle."
            diff_res = self.router.generate("diff_agent", diff_system, diff_prompt)
            artifacts["master_execution_bundle.md"] = diff_res.get("content", "")
            telemetry.append(diff_res)
            notify("diff_agent", "Master Execution Bundle packaged.", {"tokens": diff_res.get("completion_tokens", 0)})

        total_duration = round(time.time() - start_time, 2)
        logger.info("Council deliberation completed in %.2f seconds.", total_duration)

        return {
            "preset": preset,
            "status": "completed",
            "duration_seconds": total_duration,
            "artifacts": artifacts,
            "telemetry": telemetry
        }

    def persist_artifacts(self, session_id: str, artifacts: Dict[str, str], target_dir: Optional[str] = None) -> List[str]:
        """Save generated artifacts to disk."""
        out_dir = Path(target_dir) if target_dir else (self.output_dir / "sessions" / session_id)
        out_dir.mkdir(parents=True, exist_ok=True)

        saved_files = []
        for filename, content in artifacts.items():
            dest = out_dir / filename
            dest.write_text(content, encoding="utf-8")
            saved_files.append(str(dest))

        logger.info("Persisted %d artifacts to %s", len(saved_files), str(out_dir))
        return saved_files
