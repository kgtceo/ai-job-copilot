"use client";

import { useState } from "react";
import { analyze, exportCoverLetter, exportCv } from "@/lib/api";
import type { CopilotReport } from "@/lib/types";

const EXAMPLE_JD = `Senior AI Engineer (Applied LLM)
You'll own LLM features end to end: prompt pipelines, RAG, agents, evaluation,
and shipping to production. Must have: strong Python, production LLM API
experience (Anthropic/OpenAI), reliable structured output, shipped real products,
comfort across the stack, AWS + CI/CD. Nice to have: evals/LLM-as-judge,
Next.js, fine-tuning, founder experience.`;

const EXAMPLE_CV = `Kareem Ghazal — Software Engineer & Founder
Founder & Engineer, BTCBitByBit (2024–present): shipped a family Bitcoin-education
platform to real users across web, iOS, and Android from an empty repo. Backend in
Python/Django (DRF, Celery, Redis, PostgreSQL) on AWS (ECS, Terraform, CloudWatch)
with GitHub Actions CI/CD. Built a Redis sliding-window fraud-detection system and
an analytics pipeline (DAU, retention, revenue). Frontend in Next.js/TypeScript;
native iOS (Swift) and Android (Kotlin).
Skills: Python, Django, FastAPI, TypeScript, Next.js, React, PostgreSQL, Redis,
Celery, AWS, Terraform, Docker, CI/CD, Swift, Kotlin.`;

export default function Home() {
  const [jd, setJd] = useState("");
  const [cv, setCv] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [report, setReport] = useState<CopilotReport | null>(null);

  async function onAnalyze() {
    setError(null);
    setReport(null);
    setLoading(true);
    try {
      setReport(await analyze(jd, cv));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Something went wrong");
    } finally {
      setLoading(false);
    }
  }

  const canSubmit = jd.trim().length > 20 && cv.trim().length > 20 && !loading;

  return (
    <div className="container">
      <header>
        <h1>AI Job Copilot</h1>
        <p>
          Paste a job description and your CV. Get a grounded gap analysis, tailored
          résumé bullets, a cover letter, and interview prep — with evals that block
          fabrication.
        </p>
      </header>

      <div className="grid">
        <div>
          <label htmlFor="jd">Job description</label>
          <textarea id="jd" value={jd} onChange={(e) => setJd(e.target.value)} />
        </div>
        <div>
          <label htmlFor="cv">Your CV</label>
          <textarea id="cv" value={cv} onChange={(e) => setCv(e.target.value)} />
        </div>
      </div>

      <div className="actions">
        <button onClick={onAnalyze} disabled={!canSubmit}>
          {loading ? "Analysing…" : "Analyse"}
        </button>
        <button
          className="ghost"
          onClick={() => {
            setJd(EXAMPLE_JD);
            setCv(EXAMPLE_CV);
          }}
          disabled={loading}
        >
          Load example
        </button>
      </div>

      {error && <p className="error">⚠ {error}</p>}

      {report && <Report report={report} />}
    </div>
  );
}

function Report({ report }: { report: CopilotReport }) {
  const { posting, gap, resume, kit } = report;

  async function download(
    fetcher: (r: CopilotReport) => Promise<Blob>,
    filename: string,
  ) {
    try {
      const blob = await fetcher(report);
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = filename;
      a.click();
      URL.revokeObjectURL(url);
    } catch (e) {
      alert(e instanceof Error ? e.message : "PDF export failed");
    }
  }

  return (
    <>
      <section className="panel">
        <h2>
          {posting.title}
          {posting.company ? ` · ${posting.company}` : ""}
        </h2>
        <div className="score">
          <span className="big">{gap.overall_match_score}</span>
          <span>/ 100</span>
          <span className="cov">
            keyword coverage {Math.round(gap.keyword_coverage * 100)}%
          </span>
        </div>
        <p>{gap.verdict}</p>
        <div style={{ display: "flex", gap: 8, marginTop: 4 }}>
          <button onClick={() => download(exportCv, "tailored-cv.pdf")}>
            ⬇ CV PDF
          </button>
          <button
            className="ghost"
            onClick={() => download(exportCoverLetter, "cover-letter.pdf")}
          >
            ⬇ Cover letter PDF
          </button>
        </div>
        {gap.missing_skills.length > 0 && (
          <>
            <h3>Honest gaps (must-haves with no CV evidence)</h3>
            {gap.missing_skills.map((s) => (
              <span className="tag bad" key={s}>
                {s}
              </span>
            ))}
          </>
        )}
      </section>

      <section className="panel">
        <h2>Tailored résumé</h2>
        <p>{resume.summary}</p>
        {resume.bullets.map((b, i) => (
          <div className="bullet" key={i}>
            <div>{b.tailored}</div>
            {b.targets_keywords.length > 0 && (
              <div className="kw">↳ {b.targets_keywords.join(", ")}</div>
            )}
          </div>
        ))}
        <div className="panel honesty">
          <h3>Honesty note</h3>
          {resume.honesty_note}
        </div>
      </section>

      <section className="panel">
        <h2>Cover letter</h2>
        <pre className="letter">{kit.cover_letter}</pre>
      </section>

      <section className="panel">
        <h2>Interview prep</h2>
        {kit.interview_questions.map((q, i) => (
          <div className="q" key={i}>
            <strong>{q.question}</strong>
            <div className="why">
              Why: {q.why_they_ask} — Angle: {q.angle}
            </div>
          </div>
        ))}
      </section>
    </>
  );
}
