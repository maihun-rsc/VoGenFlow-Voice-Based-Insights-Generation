"""
tests/unit/test_contracts.py
Tier 1: Deterministic Contract & Invariant Test Suite.
Verifies input validation, schema invariants, and bounds checking with zero network calls.
"""

import pytest
from pydantic import BaseModel, Field, ValidationError

class SampleContract(BaseModel):
    query: str = Field(..., min_length=1, max_length=500)
    top_k: int = Field(default=5, ge=1, le=50)
    threshold: float = Field(default=0.7, ge=0.0, le=1.0)

@pytest.mark.unit
def test_contract_valid_payload():
    """Verify that a valid payload correctly instantiates the contract schema."""
    contract = SampleContract(query="valid query", top_k=10, threshold=0.85)
    assert contract.query == "valid query"
    assert contract.top_k == 10
    assert contract.threshold == 0.85

@pytest.mark.unit
def test_contract_invalid_bounds():
    """Verify that out-of-bounds inputs raise ValidationError before reaching business logic."""
    with pytest.raises(ValidationError):
        SampleContract(query="", top_k=0, threshold=1.5)
