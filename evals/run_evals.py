"""Scorecard runner: run the pipeline over a dataset, grade it, print + save.

    python evals/run_evals.py                 # deterministic checks + LLM judge
    python evals/run_evals.py --no-judge      # deterministic only (cheap, fast)
    python evals/run_evals.py --limit 1

Exit code is non-zero if any deterministic check fails, so it can gate CI.
Requires ANTHROPIC_API_KEY (it runs the real pipeline). Reports are written to
evals/reports/<timestamp>.json.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
# Make the local eval modules + the src package importable when run as a script.
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "src"))

from checks import run_all  # noqa: E402
from judge import Judge  # noqa: E402
from rich.console import Console  # noqa: E402
from rich.table import Table  # noqa: E402

from job_copilot.client import CopilotClient  # noqa: E402
from job_copilot.config import Settings  # noqa: E402
from job_copilot.pipeline import Copilot  # noqa: E402

console = Console()


def load_cases(dataset_dir: Path) -> list[dict]:
    manifest = json.loads((dataset_dir / "cases.json").read_text())
    cases = []
    for c in manifest:
        cases.append(
            {
                "name": c["name"],
                "jd": (dataset_dir / c["jd"]).resolve().read_text(),
                "cv": (dataset_dir / c["cv"]).resolve().read_text(),
            }
        )
    return cases


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", default=str(HERE / "dataset"))
    parser.add_argument("--no-judge", action="store_true", help="Skip the LLM judge.")
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()

    settings = Settings.from_env()
    client = CopilotClient(settings)
    copilot = Copilot(client)
    judge = None if args.no_judge else Judge(client)

    cases = load_cases(Path(args.dataset))
    if args.limit:
        cases = cases[: args.limit]

    results = []
    all_checks_passed = True

    for case in cases:
        with console.status(f"[bold]{case['name']}[/] — running pipeline…"):
            report = copilot.run(case["jd"], case["cv"])
            checks = run_all(report, case["cv"])
            judgement = judge.grade(report, case["jd"], case["cv"]) if judge else None

        gate = [c for c in checks if c.severity == "gate"]
        gate_passed = sum(c.passed for c in gate)
        all_checks_passed &= gate_passed == len(gate)  # advisory checks never fail the run
        results.append(
            {
                "name": case["name"],
                "match_score": report.gap.overall_match_score,
                "checks": {
                    c.name: {"passed": c.passed, "detail": c.detail, "severity": c.severity}
                    for c in checks
                },
                "gate_checks": f"{gate_passed}/{len(gate)}",
                "judge": judgement.model_dump() if judgement else None,
                "judge_mean": judgement.mean if judgement else None,
            }
        )

    _print_scorecard(results, with_judge=judge is not None)
    _save(results)
    return 0 if all_checks_passed else 1


def _print_scorecard(results: list[dict], with_judge: bool) -> None:
    table = Table(title="Eval scorecard", show_lines=True)
    table.add_column("Case")
    table.add_column("Match", justify="right")
    table.add_column("Gate checks", justify="center")
    if with_judge:
        table.add_column("Judge (mean/5)", justify="right")
    for r in results:
        row = [r["name"], str(r["match_score"]), r["gate_checks"]]
        if with_judge:
            row.append(str(r["judge_mean"]))
        table.add_row(*row)
    console.print(table)

    # Gate failures are hard fails; advisory flags are lexical warnings to review.
    for r in results:
        for name, c in r["checks"].items():
            if not c["passed"]:
                if c["severity"] == "gate":
                    console.print(f"  [red]✗ FAIL[/] {r['name']} · {name}: {c['detail']}")
                else:
                    console.print(f"  [yellow]⚠ advisory[/] {r['name']} · {name}: {c['detail']}")


def _save(results: list[dict]) -> None:
    reports_dir = HERE / "reports"
    reports_dir.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    out = reports_dir / f"{stamp}.json"
    out.write_text(json.dumps(results, indent=2))
    console.print(f"\n[dim]report → {out.relative_to(HERE.parent)}[/]")


if __name__ == "__main__":
    raise SystemExit(main())
