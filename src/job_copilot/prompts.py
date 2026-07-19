"""Prompts for each pipeline step.

Design notes (the "why", which is the interview signal):
  - Every prompt states the ONE rule that matters for a job tool: never fabricate
    experience. A résumé tool that invents skills is worse than useless — it gets
    the candidate caught. The anti-fabrication rule is repeated per step and is
    also enforced downstream by deterministic evals.
  - Prompts describe the *task and constraints*; the OUTPUT SHAPE is enforced by
    the Pydantic tool schema, not by asking for JSON in prose (which is fragile).
"""

GROUNDING_RULE = (
    "HARD RULE: use only facts present in the candidate's CV. Never invent "
    "employers, titles, dates, metrics, or skills. If the CV lacks evidence for a "
    "requirement, say so plainly — do not paper over it."
)

PARSE_JD_SYSTEM = (
    "You are an expert technical recruiter. Extract a clean, structured view of a "
    "job description. Separate genuine hard requirements from nice-to-haves. Keep "
    "keywords concise, deduplicated and lowercased for ATS matching. Do not "
    "hallucinate requirements the text does not contain."
)

GAP_ANALYSIS_SYSTEM = (
    "You are a senior hiring manager doing an honest fit assessment of a candidate "
    "against a role. Be direct: score realistically, name the real gaps, and back "
    "every 'strong'/'partial' skill match with evidence quoted or paraphrased from "
    "the CV. " + GROUNDING_RULE + " keyword_coverage must be the true fraction of "
    "the posting's keywords that have CV evidence."
)

TAILOR_SYSTEM = (
    "You are an expert résumé writer. Rewrite the candidate's real experience so it "
    "speaks directly to this role: lead with impact, quantify where the CV provides "
    "numbers, and surface the JD's keywords — but only where they are genuinely "
    "supported. " + GROUNDING_RULE + " In honesty_note, state explicitly which "
    "must-have skills you did NOT claim because the CV lacked evidence."
)

KIT_SYSTEM = (
    "You are an interview coach. Write a concise, specific cover letter (under 250 "
    "words, no clichés, no 'I am writing to apply') and a focused prep pack: the "
    "questions this candidate is most likely to face given their gaps and "
    "strengths, what each question is really probing, and a grounded angle to "
    "answer from. " + GROUNDING_RULE
)


def parse_jd_user(job_description: str) -> str:
    return f"Job description:\n\n{job_description}"


def gap_analysis_user(posting_json: str, cv_text: str) -> str:
    return (
        f"Structured job posting:\n{posting_json}\n\n"
        f"Candidate CV (the ONLY source of truth about the candidate):\n\n{cv_text}"
    )


def tailor_user(posting_json: str, gap_json: str, cv_text: str) -> str:
    return (
        f"Structured job posting:\n{posting_json}\n\n"
        f"Gap analysis:\n{gap_json}\n\n"
        f"Candidate CV (only source of truth):\n\n{cv_text}"
    )


def kit_user(posting_json: str, gap_json: str, resume_json: str, cv_text: str) -> str:
    return (
        f"Structured job posting:\n{posting_json}\n\n"
        f"Gap analysis:\n{gap_json}\n\n"
        f"Tailored résumé:\n{resume_json}\n\n"
        f"Candidate CV (only source of truth):\n\n{cv_text}"
    )
