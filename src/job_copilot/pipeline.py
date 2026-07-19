"""The copilot pipeline: JD + CV -> CopilotReport.

Four grounded steps, each a validated structured call:
  1. parse the JD into a JobPosting
  2. gap-analyse the CV against it
  3. tailor résumé bullets (grounded in the CV)
  4. build the cover letter + interview prep pack

Each step feeds the next its structured output as JSON, so later steps reason
over clean data instead of re-parsing prose. The whole thing is pure orchestration
over `CopilotClient.structured`, which keeps it trivially unit-testable with a
fake client (see tests/).
"""

from __future__ import annotations

from . import prompts
from .client import CopilotClient
from .models import (
    ApplicationKit,
    CopilotReport,
    GapAnalysis,
    JobPosting,
    TailoredResume,
)


class Copilot:
    def __init__(self, client: CopilotClient) -> None:
        self._client = client

    def parse_job(self, job_description: str) -> JobPosting:
        return self._client.structured(
            schema=JobPosting,
            system=prompts.PARSE_JD_SYSTEM,
            user=prompts.parse_jd_user(job_description),
        )

    def analyse_gap(self, posting: JobPosting, cv_text: str) -> GapAnalysis:
        return self._client.structured(
            schema=GapAnalysis,
            system=prompts.GAP_ANALYSIS_SYSTEM,
            user=prompts.gap_analysis_user(posting.model_dump_json(indent=2), cv_text),
        )

    def tailor_resume(
        self, posting: JobPosting, gap: GapAnalysis, cv_text: str
    ) -> TailoredResume:
        return self._client.structured(
            schema=TailoredResume,
            system=prompts.TAILOR_SYSTEM,
            user=prompts.tailor_user(
                posting.model_dump_json(indent=2), gap.model_dump_json(indent=2), cv_text
            ),
        )

    def build_kit(
        self,
        posting: JobPosting,
        gap: GapAnalysis,
        resume: TailoredResume,
        cv_text: str,
    ) -> ApplicationKit:
        return self._client.structured(
            schema=ApplicationKit,
            system=prompts.KIT_SYSTEM,
            user=prompts.kit_user(
                posting.model_dump_json(indent=2),
                gap.model_dump_json(indent=2),
                resume.model_dump_json(indent=2),
                cv_text,
            ),
        )

    def run(self, job_description: str, cv_text: str) -> CopilotReport:
        posting = self.parse_job(job_description)
        gap = self.analyse_gap(posting, cv_text)
        resume = self.tailor_resume(posting, gap, cv_text)
        kit = self.build_kit(posting, gap, resume, cv_text)
        return CopilotReport(posting=posting, gap=gap, resume=resume, kit=kit)
