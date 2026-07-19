"""Shared fixtures. A FakeClient returns canned structured objects so the whole
pipeline is testable offline — no API key, no network, no flakiness."""

from __future__ import annotations

import pytest

from job_copilot.models import (
    ApplicationKit,
    GapAnalysis,
    InterviewQuestion,
    JobPosting,
    SeniorityLevel,
    SkillMatch,
    TailoredBullet,
    TailoredResume,
)


class FakeClient:
    """Stands in for CopilotClient; dispatches by requested schema. Records calls."""

    def __init__(self, responses: dict[type, object]) -> None:
        self._responses = responses
        self.calls: list[type] = []

    def structured(self, *, schema, system, user, model=None):
        self.calls.append(schema)
        return self._responses[schema]


@pytest.fixture
def canned_responses() -> dict[type, object]:
    posting = JobPosting(
        title="Senior AI Engineer",
        company="Acme",
        seniority=SeniorityLevel.senior,
        must_have_skills=["Python", "LLM APIs", "evals"],
        nice_to_have_skills=["Next.js"],
        responsibilities=["Ship LLM features"],
        keywords=["python", "llm", "evals", "aws"],
    )
    gap = GapAnalysis(
        overall_match_score=82,
        verdict="Strong fit; lead with shipped production LLM work.",
        matched_skills=[
            SkillMatch(skill="Python", status="strong", evidence="Backend in Python/Django"),
            SkillMatch(skill="AWS", status="strong", evidence="Deployed on AWS (ECS, Terraform)"),
        ],
        missing_skills=["formal evals experience"],
        # 2 of 4 posting keywords (python, aws) are grounded in the test CV; llm
        # and evals are not — an honest report reports 0.5, and the deterministic
        # keyword_coverage check verifies exactly that.
        keyword_coverage=0.5,
        strengths=["Ships end to end"],
        risks=["Less formal eval tooling"],
    )
    resume = TailoredResume(
        summary="Full-stack engineer who ships production LLM-adjacent products.",
        bullets=[
            TailoredBullet(
                original="Built a fraud-detection system",
                tailored="Built a Redis sliding-window fraud system in Python on AWS.",
                targets_keywords=["python", "aws"],
            )
        ],
        honesty_note="Did not claim formal LLM-evals experience — no CV evidence.",
    )
    kit = ApplicationKit(
        cover_letter="I build and ship AI-adjacent products end to end. " * 3,
        interview_questions=[
            InterviewQuestion(
                question="How do you evaluate an LLM feature?",
                why_they_ask="Probing eval rigor.",
                angle="Deterministic checks plus LLM-as-judge.",
            )
        ],
        talking_points=["Shipped to real users across web + mobile"],
    )
    return {JobPosting: posting, GapAnalysis: gap, TailoredResume: resume, ApplicationKit: kit}
