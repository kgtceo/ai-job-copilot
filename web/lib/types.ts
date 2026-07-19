// TypeScript mirror of the backend Pydantic models (job_copilot.models).
// Kept in sync by hand; the source of truth is the Python schema + OpenAPI at /docs.

export interface SkillMatch {
  skill: string;
  status: "strong" | "partial" | "missing" | string;
  evidence: string | null;
}

export interface GapAnalysis {
  overall_match_score: number;
  verdict: string;
  matched_skills: SkillMatch[];
  missing_skills: string[];
  keyword_coverage: number;
  strengths: string[];
  risks: string[];
}

export interface JobPosting {
  title: string;
  company: string | null;
  seniority: string;
  must_have_skills: string[];
  nice_to_have_skills: string[];
  responsibilities: string[];
  keywords: string[];
}

export interface TailoredBullet {
  original: string | null;
  tailored: string;
  targets_keywords: string[];
}

export interface TailoredResume {
  summary: string;
  bullets: TailoredBullet[];
  honesty_note: string;
}

export interface InterviewQuestion {
  question: string;
  why_they_ask: string;
  angle: string;
}

export interface ApplicationKit {
  cover_letter: string;
  interview_questions: InterviewQuestion[];
  talking_points: string[];
}

export interface CopilotReport {
  posting: JobPosting;
  gap: GapAnalysis;
  resume: TailoredResume;
  kit: ApplicationKit;
}
