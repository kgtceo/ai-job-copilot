"""LLM-as-judge — grades the *subjective* quality the deterministic checks can't.

The deterministic checks (checks.py) prove the report is factually honest. The
judge grades whether it's actually *good*: is the tailoring relevant, is the cover
letter specific, is the prep pack useful — and does anything subtly overclaim
beyond what the CV supports (nuance a token-match check misses).

The judge runs on the strongest model (Opus by default, `COPILOT_JUDGE_MODEL`) so
the grader is at least as sharp as the pipeline it grades. It returns a validated
Judgement via the same forced-tool-use path as the pipeline.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from job_copilot.client import CopilotClient
from job_copilot.config import Settings
from job_copilot.models import CopilotReport


class Judgement(BaseModel):
    """1–5 rubric (5 = excellent). Every score needs a one-line rationale."""

    tailoring_relevance: int = Field(ge=1, le=5, description="Does the résumé speak to THIS role?")
    grounding: int = Field(
        ge=1, le=5, description="5 = nothing claimed beyond the CV; 1 = clear overclaiming."
    )
    cover_letter_quality: int = Field(ge=1, le=5, description="Specific, concise, non-generic?")
    interview_prep_usefulness: int = Field(ge=1, le=5)
    overall: int = Field(ge=1, le=5)
    rationale: str = Field(description="2–4 sentences justifying the scores, gaps first.")

    @property
    def mean(self) -> float:
        return round(
            (
                self.tailoring_relevance
                + self.grounding
                + self.cover_letter_quality
                + self.interview_prep_usefulness
                + self.overall
            )
            / 5,
            2,
        )


JUDGE_SYSTEM = (
    "You are a demanding hiring manager and writing coach grading an AI-generated "
    "job-application kit. Be critical and specific. The single most important axis "
    "is grounding: penalise HARD any claim, keyword, or metric that is not supported "
    "by the candidate's CV — an application that overclaims is a liability. Reward "
    "tailoring that is genuinely specific to the role, cover letters that avoid "
    "clichés, and prep that anticipates the real gaps. Score on a 1–5 rubric."
)


class Judge:
    def __init__(self, client: CopilotClient) -> None:
        self._client = client

    def grade(self, report: CopilotReport, job_description: str, cv_text: str) -> Judgement:
        user = (
            f"JOB DESCRIPTION:\n{job_description}\n\n"
            f"CANDIDATE CV (the only source of truth about the candidate):\n{cv_text}\n\n"
            f"GENERATED APPLICATION KIT (grade this):\n{report.model_dump_json(indent=2)}"
        )
        return self._client.structured(
            schema=Judgement,
            system=JUDGE_SYSTEM,
            user=user,
            model=Settings.from_env().judge_model,
        )
