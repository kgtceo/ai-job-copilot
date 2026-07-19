"""Deterministic evals — the cheap, fast, non-flaky first line of defence.

These run with NO model call. They encode the invariants a job tool must never
break, above all: *do not fabricate*. An LLM-as-judge (evals/judge.py) grades the
subjective quality on top; these grade the objective facts.

Each check takes the report + the original CV text and returns a CheckResult, so
they compose into a scorecard (evals/run_evals.py) and double as unit-test oracles.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass

from job_copilot.models import CopilotReport

_WORD = re.compile(r"[a-z0-9+#.]+")
_STOP = {"and", "the", "a", "an", "of", "to", "in", "on", "with", "for", "or", "as"}


def _tokens(text: str) -> set[str]:
    return set(_WORD.findall(text.lower()))


def _token_grounded(tok: str, cv_tokens: set[str]) -> bool:
    """True if a token appears in the CV, allowing morphological variants via a
    shared prefix (deploy/deployed/deployment, pipeline/pipelines, analytic/analytics)
    so plurals and tenses don't false-flag. Still purely LEXICAL — it cannot know
    Terraform ⟹ IaC; those synonyms are the LLM judge's job."""
    if tok in cv_tokens:
        return True
    if len(tok) < 4:
        return False
    return any(len(os.path.commonprefix([tok, c])) >= 5 for c in cv_tokens if len(c) >= 4)


def _phrase_grounded(phrase: str, cv_tokens: set[str]) -> bool:
    """A multi-word phrase is grounded if MOST of its content tokens are lexically
    present; a single token must match outright. This is a lexical LOWER BOUND —
    it flags keywords with little/no lexical support; the LLM judge is the
    authority on conceptual grounding (hence these checks are 'advisory')."""
    toks = [t for t in _tokens(phrase) if len(t) >= 3 and t not in _STOP]
    if not toks:
        return True
    hits = sum(1 for t in toks if _token_grounded(t, cv_tokens))
    return hits * 2 >= len(toks)  # at least half the content tokens


@dataclass
class CheckResult:
    name: str
    passed: bool
    detail: str
    # "gate" fails the run; "advisory" is a lexical warning (grounding nuance lives
    # in the LLM judge, which reasons about synonyms a token match can't).
    severity: str = "gate"


def check_matched_skills_have_evidence(report: CopilotReport, cv: str) -> CheckResult:
    """Every 'strong'/'partial' skill match must carry evidence."""
    offenders = [
        m.skill
        for m in report.gap.matched_skills
        if m.status in {"strong", "partial"} and not (m.evidence or "").strip()
    ]
    return CheckResult(
        "matched_skills_have_evidence",
        not offenders,
        "ok" if not offenders else f"claimed without evidence: {offenders}",
    )


def check_missing_skills_really_absent(report: CopilotReport, cv: str) -> CheckResult:
    """A 'missing' skill that is plainly in the CV means a sloppy gap analysis."""
    cv_tokens = _tokens(cv)
    false_gaps = [s for s in report.gap.missing_skills if _phrase_grounded(s, cv_tokens)]
    return CheckResult(
        "missing_skills_really_absent",
        not false_gaps,
        "ok" if not false_gaps else f"listed as missing but present in CV: {false_gaps}",
    )


def check_tailored_bullets_grounded(report: CopilotReport, cv: str) -> CheckResult:
    """The headline anti-fabrication check: every keyword a tailored bullet claims
    to surface must actually be supported by the CV text."""
    cv_tokens = _tokens(cv)
    ungrounded: list[str] = []
    for b in report.resume.bullets:
        ungrounded += [k for k in b.targets_keywords if not _phrase_grounded(k, cv_tokens)]
    return CheckResult(
        "tailored_bullets_grounded",
        not ungrounded,
        "ok"
        if not ungrounded
        else f"keywords with weak lexical CV support (review; judge grades grounding): "
        f"{sorted(set(ungrounded))}",
        severity="advisory",
    )


def check_keyword_coverage_honest(
    report: CopilotReport, cv: str, tolerance: float = 0.2
) -> CheckResult:
    """Recompute keyword coverage from the CV and compare to the model's claim."""
    keywords = report.posting.keywords
    if not keywords:
        return CheckResult("keyword_coverage_honest", True, "no keywords to score")
    cv_tokens = _tokens(cv)
    hits = sum(1 for k in keywords if _phrase_grounded(k, cv_tokens))
    actual = hits / len(keywords)
    delta = abs(actual - report.gap.keyword_coverage)
    return CheckResult(
        "keyword_coverage_honest",
        delta <= tolerance,
        f"claimed={report.gap.keyword_coverage:.2f} lexical≈{actual:.2f} delta={delta:.2f}",
        severity="advisory",
    )


def check_cover_letter_length(report: CopilotReport, cv: str, max_words: int = 260) -> CheckResult:
    words = len(report.kit.cover_letter.split())
    return CheckResult(
        "cover_letter_length",
        words <= max_words,
        f"{words} words (limit {max_words})",
    )


ALL_CHECKS = [
    check_matched_skills_have_evidence,
    check_missing_skills_really_absent,
    check_tailored_bullets_grounded,
    check_keyword_coverage_honest,
    check_cover_letter_length,
]


def run_all(report: CopilotReport, cv: str) -> list[CheckResult]:
    return [check(report, cv) for check in ALL_CHECKS]
