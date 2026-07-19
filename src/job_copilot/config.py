"""Runtime configuration.

Model choice is a deliberate, per-step decision (a real AI-eng concern), not a
single hard-coded string:
  - PARSE/TAILOR/KIT run on a fast, capable workhorse (Sonnet).
  - JUDGE (evals) runs on the strongest model (Opus) so the grader is at least as
    sharp as the thing it grades.
Override any of these via env (or a local .env) without touching code.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def _load_dotenv() -> None:
    """Load a local .env into the process env.

    Prefers python-dotenv when installed (the standard); otherwise falls back to a
    minimal built-in parser so the tool works with zero extra dependencies. Called
    at import time so both the model-override defaults below and the API key read in
    from_env() see it. Never overrides a variable already set in the real environment.
    """
    try:
        from dotenv import load_dotenv

        load_dotenv()
        return
    except ImportError:
        pass

    cwd = Path.cwd()
    for directory in (cwd, *cwd.parents):
        env_file = directory / ".env"
        if env_file.is_file():
            for line in env_file.read_text().splitlines():
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, value = line.partition("=")
                os.environ.setdefault(key.strip(), value.strip().strip("\"'"))
            return


_load_dotenv()


@dataclass(frozen=True)
class Settings:
    api_key: str
    workhorse_model: str = os.getenv("COPILOT_WORKHORSE_MODEL", "claude-sonnet-4-6")
    judge_model: str = os.getenv("COPILOT_JUDGE_MODEL", "claude-opus-4-8")
    max_tokens: int = int(os.getenv("COPILOT_MAX_TOKENS", "4096"))
    # Bounded retry when the model returns tool input that fails validation.
    max_schema_retries: int = int(os.getenv("COPILOT_MAX_SCHEMA_RETRIES", "2"))

    @classmethod
    def from_env(cls) -> "Settings":
        key = os.getenv("ANTHROPIC_API_KEY")
        if not key:
            raise RuntimeError(
                "ANTHROPIC_API_KEY is not set. Copy .env.example to .env and add your key "
                "(run from the project directory so the .env is found)."
            )
        return cls(api_key=key)
