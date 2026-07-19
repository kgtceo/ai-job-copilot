"""Typed data contracts for the copilot.

Every LLM step returns one of these Pydantic models. The models ARE the tool
schema we hand to Claude (see `client.structured`), so the model can only reply
with data that validates — no brittle string parsing, and a mismatch is caught
at the boundary and retried rather than silently propagated.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class SeniorityLevel(str, Enum):
    intern = "intern"
    junior = "junior"
    mid = "mid"
    senior = "senior"
    staff = "staff"
    lead = "lead"
    principal = "principal"
    unknown = "unknown"


# --------------------------------------------------------------------------- #
# Step 1 — parse the raw job description into structure
# --------------------------------------------------------------------------- #
class JobPosting(BaseModel):
    """Structured view of a raw job description."""

    title: str = Field(description="The role title, e.g. 'Senior AI Engineer'.")
    company: str | None = Field(
        default=None, description="Hiring company if stated, else null."
    )
    seniority: SeniorityLevel = Field(
        default=SeniorityLevel.unknown,
        description="Best-guess seniority from responsibilities/requirements.",
    )
    must_have_skills: list[str] = Field(
        default_factory=list,
        description="Hard requirements — skills/tools/experience the JD marks as required.",
    )
    nice_to_have_skills: list[str] = Field(
        default_factory=list,
        description="Preferred/bonus skills the JD lists as optional.",
    )
    responsibilities: list[str] = Field(
        default_factory=list, description="Core day-to-day responsibilities."
    )
    keywords: list[str] = Field(
        default_factory=list,
        description="ATS-relevant keywords a résumé should surface (deduped, lowercased).",
    )


# --------------------------------------------------------------------------- #
# Step 2 — gap analysis of a candidate CV against the posting
# --------------------------------------------------------------------------- #
class SkillMatch(BaseModel):
    skill: str
    status: str = Field(
        description="One of: 'strong', 'partial', 'missing' — evidence in the CV."
    )
    evidence: str | None = Field(
        default=None,
        description="Short quote/paraphrase from the CV backing a strong/partial match, "
        "or null when missing. NEVER invent evidence not present in the CV.",
    )


class GapAnalysis(BaseModel):
    overall_match_score: int = Field(
        ge=0, le=100, description="0–100 fit score for this candidate vs this posting."
    )
    verdict: str = Field(
        description="One or two sentences: should they apply, and the single biggest lever."
    )
    matched_skills: list[SkillMatch] = Field(default_factory=list)
    missing_skills: list[str] = Field(
        default_factory=list,
        description="Must-have skills with no CV evidence — the honest gaps.",
    )
    keyword_coverage: float = Field(
        ge=0.0,
        le=1.0,
        description="Fraction of JobPosting.keywords with evidence in the CV.",
    )
    strengths: list[str] = Field(default_factory=list)
    risks: list[str] = Field(
        default_factory=list,
        description="What an interviewer might probe / where the application is weak.",
    )


# --------------------------------------------------------------------------- #
# Step 3 — tailored résumé bullets (grounded in the real CV)
# --------------------------------------------------------------------------- #
class TailoredBullet(BaseModel):
    original: str | None = Field(
        default=None,
        description="The CV line this rewrites, or null if it summarises real experience.",
    )
    tailored: str = Field(
        description="Rewritten bullet aligned to the JD. STAR-shaped, quantified where the "
        "CV gives numbers. Must NOT claim experience absent from the CV."
    )
    targets_keywords: list[str] = Field(
        default_factory=list, description="JD keywords this bullet legitimately surfaces."
    )


class TailoredResume(BaseModel):
    summary: str = Field(description="2–3 sentence headline summary aimed at this role.")
    bullets: list[TailoredBullet] = Field(default_factory=list)
    honesty_note: str = Field(
        description="Explicit statement of what was NOT claimed because the CV lacked "
        "evidence — the guardrail against fabrication."
    )


# --------------------------------------------------------------------------- #
# Step 4 — cover letter + interview prep
# --------------------------------------------------------------------------- #
class InterviewQuestion(BaseModel):
    question: str
    why_they_ask: str = Field(description="What the interviewer is really probing.")
    angle: str = Field(description="A grounded angle for the candidate to answer from.")


class ApplicationKit(BaseModel):
    cover_letter: str = Field(description="A concise, specific cover letter (<250 words).")
    interview_questions: list[InterviewQuestion] = Field(default_factory=list)
    talking_points: list[str] = Field(
        default_factory=list, description="Punchy points to weave into the conversation."
    )


# --------------------------------------------------------------------------- #
# The full report the pipeline assembles
# --------------------------------------------------------------------------- #
class CopilotReport(BaseModel):
    posting: JobPosting
    gap: GapAnalysis
    resume: TailoredResume
    kit: ApplicationKit
