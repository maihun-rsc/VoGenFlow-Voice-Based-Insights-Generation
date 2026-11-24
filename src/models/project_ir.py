"""
src/models/project_ir.py
Canonical Project Intermediate Representation (ProjectIR) for VoGenFlow.
The Single Source of Truth for all generated specifications, diagrams, and exports.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class Persona(BaseModel):
    name: str = Field(..., description="Role / title of the target persona")
    role: str = Field(..., description="Primary responsibility or job description")
    pain_points: List[str] = Field(default_factory=list, description="Key frustrations addressed")
    needs: List[str] = Field(default_factory=list, description="Technical and functional requirements")


class Requirement(BaseModel):
    id: str = Field(..., description="Unique requirement ID (e.g., REQ-001)")
    title: str = Field(..., description="Short descriptive title")
    priority: str = Field(default="P0", description="Priority level: P0, P1, or P2")
    user_story: str = Field(default="", description="As a... I want to... So that...")
    acceptance_criteria: List[str] = Field(default_factory=list, description="Verifiable acceptance criteria")


class SLAMetric(BaseModel):
    metric: str = Field(..., description="Name of the SLA metric (e.g., P95 Latency)")
    target: str = Field(..., description="Target threshold (e.g., < 250ms)")
    verification_method: str = Field(..., description="How this metric is verified (e.g., Load testing)")


class ThreatEntry(BaseModel):
    threat_category: str = Field(..., description="STRIDE category: Spoofing, Tampering, Repudiation, Information Disclosure, Denial of Service, Elevation of Privilege")
    threat_description: str = Field(..., description="Specific threat description")
    mitigation: str = Field(..., description="Architectural defense or countermeasure")


class APIContract(BaseModel):
    endpoint: str = Field(..., description="HTTP Method and Route (e.g., POST /v1/projects)")
    description: str = Field(..., description="Purpose of this endpoint")
    request_payload: Optional[str] = Field(default=None, description="Schema or sample JSON request")
    response_payload: Optional[str] = Field(default=None, description="Schema or sample JSON response")


class DatabaseModel(BaseModel):
    table_name: str = Field(..., description="Name of the table or collection")
    description: str = Field(..., description="Purpose and business context of this entity")
    columns: List[str] = Field(default_factory=list, description="Column definitions with constraints")


class ArchitectureSpec(BaseModel):
    overview: str = Field(..., description="High-level architectural summary")
    topology_mermaid: str = Field(..., description="Mermaid flowchart/diagram representing container topology")
    database_ddl: str = Field(..., description="Complete PostgreSQL 16 DDL with indexes, foreign keys, RLS")
    database_models: List[DatabaseModel] = Field(default_factory=list, description="Structured entity definitions")
    api_contracts: List[APIContract] = Field(default_factory=list, description="Core API specifications")


class FailureRecoveryRow(BaseModel):
    component: str = Field(..., description="Component or service failure scenario")
    detection_sla: str = Field(..., description="Detection SLA (e.g., < 1.5s)")
    recovery_mechanism: str = Field(..., description="Automated recovery or failover action")


class LifecycleSpec(BaseModel):
    sequence_diagram_mermaid: str = Field(..., description="Mermaid sequence diagram of core transaction lifecycle")
    state_transitions_mermaid: Optional[str] = Field(default=None, description="State diagram (stateDiagram-v2)")
    failure_recovery_matrix: List[FailureRecoveryRow] = Field(default_factory=list, description="Operational resilience table")


class TaskItem(BaseModel):
    description: str = Field(..., description="Task action item")
    file_target: Optional[str] = Field(default=None, description="Specific file to create/modify")
    verification_command: Optional[str] = Field(default=None, description="Automated command to verify task")


class TaskMilestone(BaseModel):
    milestone_id: str = Field(..., description="Milestone identifier (e.g., M1, M2)")
    title: str = Field(..., description="Milestone title (e.g., Domain Models & Database Schemas)")
    tasks: List[TaskItem] = Field(default_factory=list, description="Actionable checklist items")


class UISpec(BaseModel):
    design_tokens: Dict[str, str] = Field(default_factory=dict, description="Palette and typographic tokens")
    component_hierarchy: List[str] = Field(default_factory=list, description="Core UI layout and component tree")


class ProjectIR(BaseModel):
    """The Canonical Project Intermediate Representation (Single Source of Truth)."""
    project_name: str = Field(..., description="Official name of the project")
    tagline: str = Field(default="", description="One-line elevator pitch / value proposition")
    executive_summary: str = Field(..., description="Comprehensive executive summary and problem statement")
    target_personas: List[Persona] = Field(default_factory=list, description="User personas")
    requirements: List[Requirement] = Field(default_factory=list, description="P0, P1, and P2 functional requirements")
    non_functional_slas: List[SLAMetric] = Field(default_factory=list, description="Measurable SLA targets")
    security_threat_matrix: List[ThreatEntry] = Field(default_factory=list, description="STRIDE threat matrix")
    architecture: ArchitectureSpec = Field(..., description="Complete system architecture and database DDL")
    lifecycle: LifecycleSpec = Field(..., description="Sequence flows and operational recovery matrix")
    tasks: List[TaskMilestone] = Field(default_factory=list, description="Phased engineering delivery milestones")
    ui_spec: Optional[UISpec] = Field(default=None, description="UI/UX specifications (optional)")
    constraints: List[str] = Field(default_factory=list, description="System and environmental constraints")
    assumptions: List[str] = Field(default_factory=list, description="Technical and business assumptions")
    open_questions: List[str] = Field(default_factory=list, description="Unresolved questions for human review")

    def to_prd_markdown(self) -> str:
        """Render PRD.md view from canonical ProjectIR."""
        lines = [
            f"# Product Requirements Document: {self.project_name}",
            f"> **Tagline:** {self.tagline}" if self.tagline else "",
            "",
            "## 1. Executive Summary & Problem Statement",
            self.executive_summary,
            "",
            "## 2. Target Personas",
        ]
        for p in self.target_personas:
            lines.append(f"### {p.name} ({p.role})")
            if p.pain_points:
                lines.append("**Pain Points:**")
                for pain in p.pain_points:
                    lines.append(f"- {pain}")
            if p.needs:
                lines.append("**Core Needs:**")
                for need in p.needs:
                    lines.append(f"- {need}")
            lines.append("")

        lines.extend([
            "## 3. Detailed Functional Requirements",
        ])
        for r in self.requirements:
            lines.append(f"### [{r.priority}] {r.id}: {r.title}")
            if r.user_story:
                lines.append(f"*{r.user_story}*")
            if r.acceptance_criteria:
                lines.append("**Acceptance Criteria:**")
                for ac in r.acceptance_criteria:
                    lines.append(f"- [ ] {ac}")
            lines.append("")

        if self.non_functional_slas:
            lines.extend([
                "## 4. Non-Functional SLAs Table",
                "| SLA Metric | Target SLA | Verification Method |",
                "|:---|:---|:---|",
            ])
            for sla in self.non_functional_slas:
                lines.append(f"| {sla.metric} | {sla.target} | {sla.verification_method} |")
            lines.append("")

        if self.security_threat_matrix:
            lines.extend([
                "## 5. STRIDE Security Threat Matrix",
                "| Category | Threat Description | Architectural Mitigation |",
                "|:---|:---|:---|",
            ])
            for t in self.security_threat_matrix:
                lines.append(f"| {t.threat_category} | {t.threat_description} | {t.mitigation} |")
            lines.append("")

        if self.constraints or self.assumptions:
            lines.append("## 6. Constraints & Assumptions")
            if self.constraints:
                lines.append("**Constraints:**")
                for c in self.constraints:
                    lines.append(f"- {c}")
            if self.assumptions:
                lines.append("**Assumptions:**")
                for a in self.assumptions:
                    lines.append(f"- {a}")
            lines.append("")

        return "\n".join(lines).strip()

    def to_architecture_markdown(self) -> str:
        """Render Architecture.md view from canonical ProjectIR."""
        lines = [
            f"# System Architecture Specification: {self.project_name}",
            "",
            "## 1. Architectural Overview",
            self.architecture.overview,
            "",
            "## 2. System Microservice Map & Container Topology",
            "```mermaid",
            self.architecture.topology_mermaid.strip(),
            "```",
            "",
            "## 3. Production PostgreSQL DDL Specification",
            "```sql",
            self.architecture.database_ddl.strip(),
            "```",
            "",
        ]
        if self.architecture.api_contracts:
            lines.extend([
                "## 4. Ingress API Contracts",
                "| Endpoint | Description | Request | Response |",
                "|:---|:---|:---|:---|",
            ])
            for api in self.architecture.api_contracts:
                req = f"`{api.request_payload}`" if api.request_payload else "N/A"
                res = f"`{api.response_payload}`" if api.response_payload else "N/A"
                lines.append(f"| `{api.endpoint}` | {api.description} | {req} | {res} |")
            lines.append("")

        return "\n".join(lines).strip()

    def to_flow_markdown(self) -> str:
        """Render Flow.md view from canonical ProjectIR."""
        lines = [
            f"# Systems Lifecycle & Sequence Flow: {self.project_name}",
            "",
            "## 1. End-to-End Execution Sequence",
            "```mermaid",
            self.lifecycle.sequence_diagram_mermaid.strip(),
            "```",
            "",
        ]
        if self.lifecycle.state_transitions_mermaid:
            lines.extend([
                "## 2. State Machine Transitions",
                "```mermaid",
                self.lifecycle.state_transitions_mermaid.strip(),
                "```",
                "",
            ])

        if self.lifecycle.failure_recovery_matrix:
            lines.extend([
                "## 3. Operational Failure Recovery Matrix",
                "| Component Failure | Detection SLA | Automated Recovery Mechanism |",
                "|:---|:---|:---|",
            ])
            for f in self.lifecycle.failure_recovery_matrix:
                lines.append(f"| {f.component} | {f.detection_sla} | {f.recovery_mechanism} |")
            lines.append("")

        return "\n".join(lines).strip()

    def to_tasks_markdown(self) -> str:
        """Render tasks.md view from canonical ProjectIR."""
        lines = [
            f"# Implementation Tasks & Delivery Plan: {self.project_name}",
            "",
        ]
        for m in self.tasks:
            lines.append(f"## {m.milestone_id} — {m.title}")
            for t in m.tasks:
                target_str = f" `{t.file_target}`" if t.file_target else ""
                cmd_str = f" (Verify: `{t.verification_command}`)" if t.verification_command else ""
                lines.append(f"- [ ] {t.description}{target_str}{cmd_str}")
            lines.append("")

        return "\n".join(lines).strip()

    def to_design_markdown(self) -> str:
        """Render design_proposal.md view from canonical ProjectIR."""
        if not self.ui_spec:
            return f"# Design System: {self.project_name}\n\n*No UI specification required for this service-level project.*"
        
        lines = [
            f"# Design System Specification: {self.project_name}",
            "",
            "## 1. Design System Tokens",
        ]
        for token_k, token_v in self.ui_spec.design_tokens.items():
            lines.append(f"- **{token_k}**: `{token_v}`")
        lines.append("")

        if self.ui_spec.component_hierarchy:
            lines.extend([
                "## 2. Component Hierarchy & Layout",
            ])
            for comp in self.ui_spec.component_hierarchy:
                lines.append(f"- {comp}")
            lines.append("")

        return "\n".join(lines).strip()


def create_project_ir_from_council_artifacts(transcript: str, artifacts: Dict[str, str]) -> ProjectIR:
    """Construct a canonical ProjectIR instance from council markdown outputs and transcript."""
    import re

    prd_text = artifacts.get("PRD.md", "")
    arch_text = artifacts.get("Architecture.md", "")
    flow_text = artifacts.get("Flow.md", "")
    tasks_text = artifacts.get("tasks.md", "")
    design_text = artifacts.get("design_proposal.md", "")

    title_match = re.search(r"^#\s+(?:Project Requirements Document(?:\s*\(PRD\))?[:\-]?\s*|Product Requirements Document[:\-]?\s*)(.+)$", prd_text, re.MULTILINE | re.IGNORECASE)
    if title_match:
        project_name = title_match.group(1).strip()
    else:
        project_name = transcript[:60].strip() or "VoGenFlow Engineered System"

    exec_summary = ""
    summary_match = re.search(r"###?\s+(?:Executive Summary|Problem Statement)[^\n]*\n+([\s\S]*?)(?=\n###?|\Z)", prd_text, re.IGNORECASE)
    if summary_match:
        exec_summary = summary_match.group(1).strip()
    if not exec_summary:
        exec_summary = f"Engineered system architecture for: {transcript[:200]}"

    requirements = []
    req_matches = re.findall(r"(?:###?\s*\[(P[0-2])\]\s*([^:\n]+)[:\-]?\s*(.+)|-\s*\*\*\[(P[0-2])\]\s*([^*]+)\*\*[:\-]?\s*(.+))", prd_text)
    req_idx = 1
    for m in req_matches:
        if m[0]:
            prio, title, desc = m[0], m[1].strip(), m[2].strip()
        else:
            prio, title, desc = m[3], m[4].strip(), m[5].strip()
        requirements.append(Requirement(
            id=f"REQ-{req_idx:03d}",
            title=title,
            priority=prio,
            user_story=desc,
            acceptance_criteria=[f"Verified implementation of {title}"]
        ))
        req_idx += 1

    if not requirements:
        requirements = [
            Requirement(id="REQ-001", title="Core System Service Ingestion", priority="P0", user_story="Ingest and process domain events with low latency.", acceptance_criteria=["P95 latency within SLA"]),
            Requirement(id="REQ-002", title="Multi-Tenant Data Isolation", priority="P0", user_story="Enforce tenant-level security across data layer.", acceptance_criteria=["Row-Level Security active"])
        ]

    mermaid_blocks = re.findall(r"```mermaid\n([\s\S]*?)```", arch_text)
    topology_mermaid = mermaid_blocks[0].strip() if mermaid_blocks else "flowchart TD\n    Client --> IngressGateway\n    IngressGateway --> Service\n    Service --> Database"

    sql_blocks = re.findall(r"```sql\n([\s\S]*?)```", arch_text)
    database_ddl = sql_blocks[0].strip() if sql_blocks else "-- Production PostgreSQL Schema\nCREATE TABLE IF NOT EXISTS records (\n    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),\n    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()\n);"

    architecture_spec = ArchitectureSpec(
        overview=arch_text[:300].strip() or f"High-concurrency microservice architecture for {project_name}.",
        topology_mermaid=topology_mermaid,
        database_ddl=database_ddl,
        database_models=[],
        api_contracts=[]
    )

    flow_mermaid_blocks = re.findall(r"```mermaid\n([\s\S]*?)```", flow_text)
    seq_mermaid = flow_mermaid_blocks[0].strip() if flow_mermaid_blocks else "sequenceDiagram\n    Client->>Gateway: Request\n    Gateway->>DB: Query\n    DB-->>Client: Result"
    state_mermaid = flow_mermaid_blocks[1].strip() if len(flow_mermaid_blocks) > 1 else None

    lifecycle_spec = LifecycleSpec(
        sequence_diagram_mermaid=seq_mermaid,
        state_transitions_mermaid=state_mermaid,
        failure_recovery_matrix=[
            FailureRecoveryRow(component="Database Primary Failover", detection_sla="< 3.0s", recovery_mechanism="Automatic promotion of hot standby replica via Patroni"),
            FailureRecoveryRow(component="Upstream Network Partition", detection_sla="< 500ms", recovery_mechanism="Circuit breaker opens and sheds background load")
        ]
    )

    task_milestones = []
    milestone_matches = re.findall(r"##\s+(?:Milestone\s+\d+:?|Sprint\s+\d+:?|Phase\s+\d+:?)\s*([^\n]+)\n+([\s\S]*?)(?=\n##|\Z)", tasks_text, re.IGNORECASE)
    m_idx = 1
    for m_title, m_body in milestone_matches:
        task_items = []
        for line in m_body.splitlines():
            line = line.strip()
            if line.startswith("- [ ]") or line.startswith("* [ ]"):
                desc = line[5:].strip()
                target = None
                target_m = re.search(r"`([^`]+)`", desc)
                if target_m:
                    target = target_m.group(1)
                task_items.append(TaskItem(description=desc, file_target=target))
        if task_items:
            task_milestones.append(TaskMilestone(milestone_id=f"M{m_idx}", title=m_title.strip(), tasks=task_items))
            m_idx += 1

    if not task_milestones:
        task_milestones = [
            TaskMilestone(milestone_id="M1", title="Core Domain Schemas", tasks=[TaskItem(description="Create domain models and database tables", file_target="migrations/001_schema.sql")]),
            TaskMilestone(milestone_id="M2", title="Service Gateway & API", tasks=[TaskItem(description="Implement route handlers and authentication", file_target="src/main.py")])
        ]

    ui_spec = None
    if design_text and "Design Tokens" in design_text:
        ui_spec = UISpec(
            design_tokens={
                "--bg-canvas": "#000000",
                "--bg-surface": "#0A0A0A",
                "--accent-gold": "#D4AF37",
                "--text-primary": "#EDEDED"
            },
            component_hierarchy=["HeaderNavigationBar", "MainWorkspaceCanvas", "SpecificationTabs", "ExportToolbar"]
        )

    return ProjectIR(
        project_name=project_name,
        tagline=f"Next-Generation Architecture for {project_name}",
        executive_summary=exec_summary,
        target_personas=[
            Persona(name="Lead Engineer", role="Systems Architect", pain_points=["Unreliable specs", "Rate-limit stalls"], needs=["Deterministic DDL", "Type-safe schemas"]),
            Persona(name="Product Lead", role="Technical PM", pain_points=["Document drift between PRD and Architecture"], needs=["Canonical single source of truth"])
        ],
        requirements=requirements,
        non_functional_slas=[
            SLAMetric(metric="P95 Latency", target="< 50ms", verification_method="OpenTelemetry tracing"),
            SLAMetric(metric="Availability", target="99.99%", verification_method="Multi-AZ health checks")
        ],
        security_threat_matrix=[
            ThreatEntry(threat_category="Information Disclosure", threat_description="Tenant cross-boundary data leakage", mitigation="Row-Level Security (RLS) on all PostgreSQL tables"),
            ThreatEntry(threat_category="Denial of Service", threat_description="High-frequency API burst saturation", mitigation="Token bucket rate pacing and circuit breaker")
        ],
        architecture=architecture_spec,
        lifecycle=lifecycle_spec,
        tasks=task_milestones,
        ui_spec=ui_spec
    )
