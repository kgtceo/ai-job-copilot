"""The deterministic evals must PASS a grounded report and CATCH fabrication."""

from __future__ import annotations

import sys
from pathlib import Path

# evals/ is a sibling of tests/, not an installed package.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "evals"))

from checks import (  # noqa: E402
    check_missing_skills_really_absent,
    check_tailored_bullets_grounded,
    run_all,
)
from job_copilot.models import (  # noqa: E402
    ApplicationKit,
    CopilotReport,
    GapAnalysis,
    JobPosting,
    TailoredBullet,
    TailoredResume,
)

CV = "Backend in Python and Django, deployed on AWS with Terraform. Built Redis systems."


def _report(canned) -> CopilotReport:
    return CopilotReport(
        posting=canned[JobPosting],
        gap=canned[GapAnalysis],
        resume=canned[TailoredResume],
        kit=canned[ApplicationKit],
    )


def test_grounded_report_passes_all(canned_responses):
    report = _report(canned_responses)
    results = run_all(report, CV)
    failed = [r for r in results if not r.passed]
    assert not failed, f"grounded report should pass all checks, failed: {failed}"


def test_catches_fabricated_keyword(canned_responses):
    report = _report(canned_responses)
    # Inject a keyword the CV never supports.
    report.resume.bullets.append(
        TailoredBullet(tailored="Led Kubernetes migration", targets_keywords=["kubernetes"])
    )
    result = check_tailored_bullets_grounded(report, CV)
    assert not result.passed
    assert "kubernetes" in result.detail


def test_catches_false_missing_gap(canned_responses):
    report = _report(canned_responses)
    # 'Python' is clearly in the CV — flagging it as missing is a bad gap analysis.
    report.gap.missing_skills.append("Python")
    result = check_missing_skills_really_absent(report, CV)
    assert not result.passed


def test_morphology_does_not_false_flag():
    """Plurals/tenses and multi-word concepts shouldn't false-flag; genuinely
    absent terms still should."""
    from checks import _phrase_grounded, _tokens

    cv = _tokens("deployed an analytics pipeline on aws with terraform")
    assert _phrase_grounded("analytics pipelines", cv)  # pipelines ~ pipeline
    assert _phrase_grounded("cloud deployment", cv)  # deployment ~ deployed (majority)
    assert not _phrase_grounded("kubernetes orchestration", cv)  # neither supported


def test_grounding_check_is_advisory(canned_responses):
    """Grounding is a lexical warning, not a hard gate — the LLM judge owns it."""
    report = _report(canned_responses)
    report.resume.bullets.append(
        TailoredBullet(tailored="x", targets_keywords=["kubernetes"])
    )
    result = check_tailored_bullets_grounded(report, CV)
    assert not result.passed
    assert result.severity == "advisory"
