"""The Judgement rubric validates and averages correctly (offline — no model)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
from pydantic import ValidationError

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "evals"))

from judge import Judgement  # noqa: E402


def test_mean_is_average_of_five_dimensions():
    j = Judgement(
        tailoring_relevance=4,
        grounding=5,
        cover_letter_quality=3,
        interview_prep_usefulness=4,
        overall=4,
        rationale="Solid, well grounded.",
    )
    assert j.mean == 4.0


def test_scores_are_bounded_1_to_5():
    with pytest.raises(ValidationError):
        Judgement(
            tailoring_relevance=6,  # out of range
            grounding=5,
            cover_letter_quality=3,
            interview_prep_usefulness=4,
            overall=4,
            rationale="x",
        )
