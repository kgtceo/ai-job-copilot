"""`job-copilot` CLI — the fastest way to demo the tool without a frontend.

    job-copilot run --jd examples/sample_jd.md --cv examples/sample_cv.md
    job-copilot run --jd jd.md --cv cv.md --json > report.json
"""

from __future__ import annotations

import json
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from .client import CopilotClient
from .config import Settings
from .pipeline import Copilot

app = typer.Typer(add_completion=False, help="AI copilot for your job search.")
console = Console()


@app.callback()
def _root() -> None:
    """AI copilot for your job search.

    A callback (even a no-op) keeps Typer in multi-command mode, so `run` is a
    real subcommand rather than being collapsed into a single-command program.
    """


@app.command()
def run(
    jd: Path = typer.Option(..., exists=True, readable=True, help="Job description file."),
    cv: Path = typer.Option(..., exists=True, readable=True, help="Your CV file."),
    as_json: bool = typer.Option(False, "--json", help="Emit the full report as JSON."),
    cv_pdf: Path = typer.Option(None, "--cv-pdf", help="Write the tailored résumé PDF here."),
    cover_pdf: Path = typer.Option(
        None, "--cover-pdf", help="Write the cover letter PDF here."
    ),
) -> None:
    """Run the full copilot pipeline over a JD + CV and print the report."""
    copilot = Copilot(CopilotClient(Settings.from_env()))
    with console.status("[bold]Analysing…[/] parsing JD → gap → tailoring → prep pack"):
        report = copilot.run(jd.read_text(), cv.read_text())

    if cv_pdf is not None:
        from .pdf import render_resume_pdf

        cv_pdf.write_bytes(render_resume_pdf(report))
        console.print(f"[green]✓ Résumé PDF → {cv_pdf}[/]")
    if cover_pdf is not None:
        from .pdf import render_cover_letter_pdf

        cover_pdf.write_bytes(render_cover_letter_pdf(report))
        console.print(f"[green]✓ Cover letter PDF → {cover_pdf}[/]")

    if as_json:
        typer.echo(report.model_dump_json(indent=2))
        return

    g = report.gap
    console.print(
        Panel.fit(
            f"[bold]{report.posting.title}[/]"
            + (f" @ {report.posting.company}" if report.posting.company else "")
            + f"\n\n[bold]{g.overall_match_score}/100[/]  ·  "
            f"keyword coverage {g.keyword_coverage:.0%}\n{g.verdict}",
            title="Match",
            border_style="cyan",
        )
    )

    if g.missing_skills:
        console.print("\n[bold red]Honest gaps (must-haves with no CV evidence):[/]")
        for s in g.missing_skills:
            console.print(f"  • {s}")

    table = Table(title="\nTailored résumé bullets", show_lines=True)
    table.add_column("Rewritten (grounded in your CV)", overflow="fold")
    table.add_column("Keywords", overflow="fold", style="dim")
    for b in report.resume.bullets:
        table.add_row(b.tailored, ", ".join(b.targets_keywords))
    console.print(table)

    console.print(
        Panel(report.resume.honesty_note, title="Honesty note", border_style="yellow")
    )
    console.print(Panel(report.kit.cover_letter, title="Cover letter", border_style="green"))

    console.print("\n[bold]Likely interview questions:[/]")
    for q in report.kit.interview_questions:
        console.print(f"  [bold]Q:[/] {q.question}\n     [dim]why:[/] {q.why_they_ask}")


if __name__ == "__main__":
    app()
