"""The pipeline orchestrates four structured calls, in order, and assembles a
CopilotReport. Verified with a fake client — no network."""

from __future__ import annotations

from job_copilot.models import (
    ApplicationKit,
    CopilotReport,
    GapAnalysis,
    JobPosting,
    TailoredResume,
)
from job_copilot.pipeline import Copilot

from conftest import FakeClient


def test_run_calls_all_four_steps_in_order(canned_responses):
    client = FakeClient(canned_responses)
    report = Copilot(client).run("some JD", "some CV")

    assert isinstance(report, CopilotReport)
    assert client.calls == [JobPosting, GapAnalysis, TailoredResume, ApplicationKit]


def test_run_assembles_the_report(canned_responses):
    report = Copilot(FakeClient(canned_responses)).run("jd", "cv")
    assert report.posting.title == "Senior AI Engineer"
    assert report.gap.overall_match_score == 82
    assert report.resume.bullets[0].targets_keywords == ["python", "aws"]
    assert report.kit.interview_questions
