"""The PDF renderer produces a valid, non-trivial PDF from a report (offline)."""

from __future__ import annotations

import pytest

pytest.importorskip("fpdf")  # skip if fpdf2 isn't installed in this env

from job_copilot.models import CopilotReport  # noqa: E402
from job_copilot.pdf import render_cover_letter_pdf, render_resume_pdf  # noqa: E402


def _report(canned) -> CopilotReport:
    from job_copilot.models import (
        ApplicationKit,
        GapAnalysis,
        JobPosting,
        TailoredResume,
    )

    return CopilotReport(
        posting=canned[JobPosting],
        gap=canned[GapAnalysis],
        resume=canned[TailoredResume],
        kit=canned[ApplicationKit],
    )


def test_resume_pdf_is_valid(canned_responses):
    data = render_resume_pdf(_report(canned_responses))
    assert isinstance(data, bytes)
    assert data.startswith(b"%PDF")  # PDF magic header
    assert len(data) > 800  # not an empty shell


def test_cover_letter_pdf_is_valid(canned_responses):
    data = render_cover_letter_pdf(_report(canned_responses))
    assert data.startswith(b"%PDF")
    assert len(data) > 800


def test_handles_smart_punctuation(canned_responses):
    report = _report(canned_responses)
    # em-dash, curly quotes, ellipsis — must not raise on the Latin-1 core font.
    report.kit.cover_letter = "I’ve shipped — end to end — “real” products…"
    assert render_cover_letter_pdf(report).startswith(b"%PDF")
