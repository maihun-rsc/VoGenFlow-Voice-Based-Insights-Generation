"""
tests/unit/test_prompt_compiler_unit.py
Tier 1: Deterministic Unit Test Suite for MasterPromptCompiler.

Verifies Zero-Shot Intermediate Representation (IR) assembly, section header integrity,
unbalanced code fence detection, and metadata compilation with zero network calls.
"""

import pytest
from src.master_prompt_compiler import MasterPromptCompiler


@pytest.mark.unit
class TestMasterPromptCompiler:
    """Rigorous tests for MasterPromptCompiler compilation and syntax validation."""

    def test_compiler_initialization(self):
        """Verify compiler instantiates cleanly."""
        compiler = MasterPromptCompiler()
        assert compiler is not None

    def test_compile_bundle_with_complete_artifacts(self):
        """Verify compile() generates a complete bundle containing all artifact sections."""
        compiler = MasterPromptCompiler()
        artifacts = {
            "PRD.md": "# Product Requirements\nDeliver a real-time speech analytics microservice.",
            "Architecture.md": "# System Architecture\nFastAPI gateway with Redis pubsub and Postgres.",
            "design_proposal.md": "# UI/UX Design\nDark luxury aesthetic with gold accents.",
            "Flow.md": "# Systems Flow\nAudio chunking -> Whisper STT -> Council DAG -> Dispatch.",
            "tasks.md": "# Action Tasks\n- [ ] Configure database\n- [ ] Deploy container",
        }

        bundle = compiler.compile(
            session_id="session_test_42",
            artifacts=artifacts,
            target_branch="feature/realtime-stt",
            project_name="Vo-Gen-Flow-Enterprise"
        )

        assert "MASTER EXECUTION BUNDLE: VO-GEN-FLOW-ENTERPRISE" in bundle
        assert "SESSION ID: session_test_42" in bundle
        assert "TARGET BRANCH: feature/realtime-stt" in bundle
        assert "Deliver a real-time speech analytics microservice." in bundle
        assert "FastAPI gateway with Redis pubsub and Postgres." in bundle
        assert "Dark luxury aesthetic with gold accents." in bundle
        assert "Audio chunking -> Whisper STT -> Council DAG -> Dispatch." in bundle
        assert "- [ ] Configure database" in bundle
        assert "Automated Verification Matrix" in bundle

    def test_compile_bundle_with_missing_artifacts_uses_defaults(self):
        """Verify compile() falls back gracefully to defaults when artifacts are missing."""
        compiler = MasterPromptCompiler()
        bundle = compiler.compile(session_id="empty_session", artifacts={})

        assert "MASTER EXECUTION BUNDLE" in bundle
        assert "No PRD specified." in bundle
        assert "No architecture specified." in bundle
        assert "Standard Linear tokens." in bundle
        assert "Standard async sequence." in bundle
        assert "- [ ] Initial setup" in bundle

    def test_validate_bundle_clean(self):
        """Verify validate_bundle() returns valid=True and zero errors on clean compiled output."""
        compiler = MasterPromptCompiler()
        bundle = compiler.compile(session_id="valid_sess", artifacts={})
        validation = compiler.validate_bundle(bundle)

        assert validation["valid"] is True
        assert len(validation["errors"]) == 0
        assert validation["char_count"] > 100
        assert validation["line_count"] > 20

    def test_validate_bundle_detects_unbalanced_code_fences(self):
        """Verify validate_bundle() catches odd number of markdown code fences."""
        compiler = MasterPromptCompiler()
        bundle = compiler.compile(session_id="fence_test", artifacts={})

        # Inject an extra unclosed code fence at the beginning of a line
        malformed_bundle = bundle + "\n```python\nprint('unclosed code block')\n"
        validation = compiler.validate_bundle(malformed_bundle)

        assert validation["valid"] is False
        assert any("Unbalanced markdown code blocks" in err for err in validation["errors"])

    def test_validate_bundle_detects_missing_mandatory_headers(self):
        """Verify validate_bundle() flags omission of required section headers."""
        compiler = MasterPromptCompiler()
        required_headers = [
            "MASTER EXECUTION BUNDLE",
            "High-Level & Low-Level Design Specification",
            "System Architecture & Relational Database Schemas",
            "Granular Action Checklist & File Declarations",
            "Automated Verification Matrix"
        ]

        base_bundle = compiler.compile(session_id="header_test", artifacts={})

        for hdr in required_headers:
            tampered_bundle = base_bundle.replace(hdr, "REPLACED_HEADER")
            validation = compiler.validate_bundle(tampered_bundle)
            assert validation["valid"] is False
            assert any(hdr in err for err in validation["errors"])

    def test_validate_bundle_empty_string(self):
        """Verify validate_bundle() rejects empty string with all mandatory header errors."""
        compiler = MasterPromptCompiler()
        validation = compiler.validate_bundle("")

        assert validation["valid"] is False
        assert len(validation["errors"]) >= 5
        assert validation["char_count"] == 0
        assert validation["line_count"] == 0

    def test_compile_bundle_custom_metadata(self):
        """Verify custom project names and branch names are uppercase and formatted correctly."""
        compiler = MasterPromptCompiler()
        bundle = compiler.compile(
            session_id="custom_meta_01",
            artifacts={"PRD.md": "PRD content"},
            target_branch="dev-release",
            project_name="my-custom-saas"
        )
        assert "MASTER EXECUTION BUNDLE: MY-CUSTOM-SAAS" in bundle
        assert "TARGET BRANCH: dev-release" in bundle
        assert "SESSION ID: custom_meta_01" in bundle
