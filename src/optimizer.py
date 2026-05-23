"""
حلقه اصلی بهینه‌سازی پرامپت طراحی داخلی — بدون نیاز به Anthropic API
Main optimization loop — FAL_KEY only
"""

from datetime import datetime
from typing import Dict, List, Optional

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.table import Table
from rich import box

from config import FAL_MODELS, PROMPT_FORMATS
from src.prompt_generator import generate_prompt_formats, display_prompt_formats
from src.image_generator import generate_images_for_formats, display_generation_summary
from src.evaluator import evaluate_images_manually, display_evaluation_results, EvaluationScore
from src.results_tracker import ResultsTracker

console = Console()


def _select_models() -> List[str]:
    """انتخاب مدل‌های Fal.ai"""
    console.print("\n[bold cyan]Available Models:[/bold cyan]")
    model_list = list(FAL_MODELS.keys())
    for i, name in enumerate(model_list, 1):
        console.print(f"  [magenta]{i}.[/magenta] {name}  [dim]({FAL_MODELS[name]})[/dim]")

    console.print("\n[dim]Enter numbers separated by comma — default: 1,2 (flux-pro + flux-dev)[/dim]")
    choice = Prompt.ask("Select models", default="1,2")

    selected = []
    for part in choice.split(","):
        part = part.strip()
        if part.isdigit():
            idx = int(part) - 1
            if 0 <= idx < len(model_list):
                selected.append(model_list[idx])

    if not selected:
        selected = ["flux-pro", "flux-dev"]

    console.print(f"[green]Selected: {', '.join(selected)}[/green]")
    return selected


def _show_patterns(tracker: ResultsTracker) -> None:
    """نمایش الگوهای برنده از تاریخچه"""
    analytics = tracker.get_analytics()
    if not analytics or not analytics.get("top_combinations"):
        return

    table = Table(title="Historical Best Combinations", box=box.SIMPLE, border_style="yellow")
    table.add_column("Combo", style="white")
    table.add_column("Avg Score", justify="center", style="bold yellow")

    for combo in analytics["top_combinations"][:3]:
        table.add_row(combo["combo"], f"{combo['avg_score']:.1f}/10")

    console.print(table)


def run_optimization_loop(fal_key: str) -> None:
    """
    حلقه اصلی بهینه‌سازی
    Main loop: concept → formats → generate → user rates → track → repeat
    """
    tracker = ResultsTracker()
    session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    iteration = 1

    if tracker.history:
        console.print(f"[dim]Loaded {len(tracker.history)} historical records.[/dim]")
        _show_patterns(tracker)

    while True:
        console.print(Panel(
            f"[bold cyan]Optimization Round #{iteration}[/bold cyan]",
            border_style="cyan",
            expand=False,
        ))

        # ── دریافت مفهوم ──────────────────────────────────────────────────
        concept = Prompt.ask(
            "\n[bold]Interior design concept[/bold]",
            default="A modern minimalist living room with warm lighting and natural wood",
        )

        # ── تولید فرمت‌ها ─────────────────────────────────────────────────
        formats = generate_prompt_formats(concept)
        display_prompt_formats(formats, concept)

        # ── انتخاب مدل ────────────────────────────────────────────────────
        selected_models = _select_models()

        total = len(formats) * len(selected_models)
        if not Confirm.ask(
            f"\nGenerate [bold]{total} images[/bold] "
            f"({len(formats)} formats × {len(selected_models)} models)?",
            default=True,
        ):
            continue

        # ── تولید تصاویر ──────────────────────────────────────────────────
        generation_results = generate_images_for_formats(
            formats=formats,
            selected_models=selected_models,
            concept=concept,
            fal_key=fal_key,
        )
        display_generation_summary(generation_results)

        successful = [r for r in generation_results if r.success]
        if not successful:
            console.print("[red]No images generated. Check your FAL_KEY and try again.[/red]")
            if Confirm.ask("Retry?", default=True):
                continue
            break

        # ── ارزیابی دستی ──────────────────────────────────────────────────
        scores = evaluate_images_manually(generation_results, concept)
        if not scores:
            continue

        # ── نمایش رتبه‌بندی ───────────────────────────────────────────────
        display_evaluation_results(scores)

        # ── ذخیره نتایج ───────────────────────────────────────────────────
        for s in scores:
            tracker.add_result(
                concept=concept,
                format_type=s.format_name,
                format_name=PROMPT_FORMATS.get(s.format_name, s.format_name),
                prompt_text=s.prompt_text,
                model=s.model_name,
                image_path=s.image_path or None,
                scores={
                    "design_coherence": s.design_coherence,
                    "interior_quality": s.interior_quality,
                    "aesthetic_appeal": s.aesthetic_appeal,
                    "technical_quality": s.technical_quality,
                    "usability": s.usability,
                    "total": s.total_score,
                },
                user_rating=int(s.total_score),
                iteration=iteration,
                session_id=session_id,
            )

        # ── نمایش تحلیل تجمعی ────────────────────────────────────────────
        _show_patterns(tracker)

        iteration += 1

        if not Confirm.ask(f"\nRun round #{iteration}?", default=True):
            break

    console.print(Panel(
        f"[bold green]Session complete — {iteration - 1} round(s) done.[/bold green]\n"
        "[dim]Results saved to results/history.json[/dim]",
        border_style="green",
    ))

    if Confirm.ask("Show full history summary?", default=True):
        tracker.generate_summary_report()
