"""FastAPI service exposing the copilot pipeline.

    uvicorn job_copilot.api:app --reload        # docs at http://localhost:8000/docs

One endpoint does the work: POST /api/analyze {job_description, cv_text} ->
CopilotReport. The response model is the same Pydantic type the pipeline produces,
so the OpenAPI schema at /docs is generated for free and always in sync.
"""

from __future__ import annotations

import os

from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from .client import CopilotClient, StructuredCallError
from .config import Settings
from .models import CopilotReport
from .pipeline import Copilot

app = FastAPI(
    title="ai-job-copilot",
    version="0.1.0",
    description="Grounded, evaluated LLM pipeline that tailors a CV to a job description.",
)

# Comma-separated allowlist (set for production, e.g. your Vercel URL). In dev we
# also allow any localhost port via regex, since Next falls back to 3001/3002 when
# 3000 is busy — a common cause of a "Failed to fetch" that's really a CORS block.
_origins = os.getenv("COPILOT_CORS_ORIGINS", "").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in _origins if o.strip()],
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1):\d+",
    allow_methods=["*"],
    allow_headers=["*"],
)

# Built once and reused; construction validates the API key is present.
_copilot: Copilot | None = None


def _get_copilot() -> Copilot:
    global _copilot
    if _copilot is None:
        _copilot = Copilot(CopilotClient(Settings.from_env()))
    return _copilot


class AnalyzeRequest(BaseModel):
    job_description: str = Field(min_length=20, description="Raw job description text.")
    cv_text: str = Field(min_length=20, description="The candidate's CV text.")


@app.get("/health")
def health() -> dict[str, bool]:
    return {"ok": True, "configured": bool(os.getenv("ANTHROPIC_API_KEY"))}


@app.post("/api/analyze", response_model=CopilotReport)
def analyze(req: AnalyzeRequest) -> CopilotReport:
    try:
        return _get_copilot().run(req.job_description, req.cv_text)
    except StructuredCallError as exc:
        # The model couldn't produce schema-valid output within the retry budget.
        raise HTTPException(status_code=502, detail=f"model output error: {exc}") from exc
    except RuntimeError as exc:
        # e.g. missing API key.
        raise HTTPException(status_code=500, detail=str(exc)) from exc


def _pdf_response(data: bytes, filename: str) -> Response:
    return Response(
        content=data,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@app.post("/api/export/cv")
def export_cv(report: CopilotReport) -> Response:
    """Tailored résumé PDF (the client already has the report from /api/analyze)."""
    from .pdf import render_resume_pdf

    return _pdf_response(render_resume_pdf(report), "tailored-cv.pdf")


@app.post("/api/export/cover-letter")
def export_cover_letter(report: CopilotReport) -> Response:
    """Cover letter PDF."""
    from .pdf import render_cover_letter_pdf

    return _pdf_response(render_cover_letter_pdf(report), "cover-letter.pdf")
