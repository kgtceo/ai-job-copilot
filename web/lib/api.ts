import type { CopilotReport } from "./types";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export async function analyze(
  jobDescription: string,
  cvText: string,
): Promise<CopilotReport> {
  const res = await fetch(`${API_URL}/api/analyze`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ job_description: jobDescription, cv_text: cvText }),
  });

  if (!res.ok) {
    let detail = `Request failed (${res.status})`;
    try {
      const body = await res.json();
      if (body?.detail) detail = body.detail;
    } catch {
      /* non-JSON error body */
    }
    throw new Error(detail);
  }

  return res.json();
}

async function exportPdf(
  doc: "cv" | "cover-letter",
  report: CopilotReport,
): Promise<Blob> {
  const res = await fetch(`${API_URL}/api/export/${doc}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(report),
  });
  if (!res.ok) throw new Error(`PDF export failed (${res.status})`);
  return res.blob();
}

export const exportCv = (report: CopilotReport) => exportPdf("cv", report);
export const exportCoverLetter = (report: CopilotReport) =>
  exportPdf("cover-letter", report);
