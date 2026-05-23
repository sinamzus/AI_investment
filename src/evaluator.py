"""
ارزیابی دستی تصاویر توسط کاربر
Manual user evaluation of generated images — no external API needed
"""

from dataclasses import dataclass
from typing import Optional
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import IntPrompt
from rich import box

console = Console()


@dataclass
class EvaluationScore:
    """نتیجه ارزیابی یک تصویر"""
    format_name: str
    model_name: str
    prompt_text: str
    image_path: str
    image_url: str
    total_score: float
    concept: str
    reasoning: str = ""

    # معیارهای جزئی (اختیاری — در حالت دستی همه برابر total هستند)
    design_coherence: float = 0.0
    interior_quality: float = 0.0
    aesthetic_appeal: float = 0.0
    technical_quality: float = 0.0
    usability: float = 0.0


def evaluate_images_manually(
    generation_results: list,
    concept: str,
) -> list[EvaluationScore]:
    """
    نمایش URL تصاویر و دریافت امتیاز دستی از کاربر
    Show image URLs and collect user ratings (1-10)
    """
    successful = [r for r in generation_results if r.success and r.image_url]

    if not successful:
        console.print("[red]No successful images to evaluate.[/red]")
        return []

    console.print(Panel(
        "[bold cyan]Manual Evaluation[/bold cyan]\n\n"
        "Open each image URL in your browser and rate it from 1 to 10.\n"
        "[dim]1 = poor  |  5 = acceptable  |  10 = excellent[/dim]",
        border_style="cyan",
    ))

    scores = []

    for i, result in enumerate(successful, 1):
        from src.prompt_generator import FORMAT_DESCRIPTIONS
        fmt_desc = FORMAT_DESCRIPTIONS.get(result.format_name, result.format_name)

        console.print(f"\n[bold]Image {i} of {len(successful)}[/bold]")
        console.print(f"  Model:  [cyan]{result.model_name}[/cyan]")
        console.print(f"  Format: [magenta]{result.format_name}[/magenta] — [dim]{fmt_desc}[/dim]")
        console.print(f"  URL:    [link={result.image_url}]{result.image_url}[/link]")
        console.print(f"  [dim]Prompt: {result.prompt_text[:100]}...[/dim]" if len(result.prompt_text) > 100 else f"  [dim]Prompt: {result.prompt_text}[/dim]")

        rating = IntPrompt.ask(
            "  [bold yellow]Your rating (1-10)[/bold yellow]",
            default=5,
        )
        rating = max(1, min(10, rating))

        scores.append(EvaluationScore(
            format_name=result.format_name,
            model_name=result.model_name,
            prompt_text=result.prompt_text,
            image_path=result.image_path or "",
            image_url=result.image_url,
            total_score=float(rating),
            concept=concept,
            design_coherence=float(rating),
            interior_quality=float(rating),
            aesthetic_appeal=float(rating),
            technical_quality=float(rating),
            usability=float(rating),
        ))

    return scores


def display_evaluation_results(scores: list[EvaluationScore]) -> None:
    """نمایش نتایج ارزیابی رتبه‌بندی‌شده"""
    sorted_scores = sorted(scores, key=lambda s: s.total_score, reverse=True)

    table = Table(
        title="Results — Ranked by Your Rating",
        box=box.ROUNDED,
        border_style="cyan",
        show_lines=True,
    )
    table.add_column("Rank", justify="center", style="bold")
    table.add_column("Model", style="cyan", no_wrap=True)
    table.add_column("Format", style="magenta")
    table.add_column("Score", justify="center", style="bold yellow")
    table.add_column("Image URL", style="dim")

    for i, s in enumerate(sorted_scores, 1):
        rank_label = {1: "[gold1]#1[/gold1]", 2: "[silver]#2[/silver]", 3: "[dark_orange]#3[/dark_orange]"}.get(i, f"#{i}")
        color = "green" if s.total_score >= 7 else "yellow" if s.total_score >= 5 else "red"
        table.add_row(
            rank_label,
            s.model_name,
            s.format_name,
            f"[{color}]{s.total_score:.0f}/10[/{color}]",
            s.image_url[:60] + "..." if len(s.image_url) > 60 else s.image_url,
        )

    console.print(table)

    if sorted_scores:
        best = sorted_scores[0]
        console.print(Panel(
            f"[bold yellow]Winner: {best.model_name} + {best.format_name} — {best.total_score:.0f}/10[/bold yellow]\n"
            f"[dim]{best.image_url}[/dim]",
            title="Best Result",
            border_style="yellow",
        ))
