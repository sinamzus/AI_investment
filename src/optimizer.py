"""
حلقه اصلی بهینه‌سازی پرامپت طراحی داخلی
Main optimization loop for interior design prompt engineering
"""

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.table import Table
from rich import box

from config import FAL_MODELS, PROMPT_FORMATS
from src.prompt_generator import generate_prompt_formats, display_prompt_formats
from src.image_generator import generate_images_for_formats, display_generation_summary
from src.evaluator import evaluate_image, display_evaluation_results
from src.results_tracker import (
    save_round_results,
    display_analytics,
    get_winning_patterns,
)

console = Console()


def _select_models() -> list[str]:
    """انتخاب مدل‌های Fal.ai توسط کاربر"""
    console.print("\n[bold cyan]Available Models:[/bold cyan]")
    model_list = list(FAL_MODELS.keys())

    for i, name in enumerate(model_list, 1):
        console.print(f"  [magenta]{i}.[/magenta] {name} ({FAL_MODELS[name]})")

    console.print("\n[dim]Enter model numbers separated by comma (e.g. 1,2) or press Enter for flux-pro + flux-dev[/dim]")
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

    console.print(f"[green]Selected models: {', '.join(selected)}[/green]")
    return selected


def _get_user_favorites(scores: list) -> tuple[list[str], str]:
    """دریافت انتخاب‌های کاربر از میان نتایج"""
    if not scores:
        return [], ""

    console.print("\n[bold cyan]Which results did you like most?[/bold cyan]")
    console.print("[dim]Enter combinations like: flux-pro/FORMAT_A, flux-dev/FORMAT_C[/dim]")
    console.print("[dim]Or press Enter to skip[/dim]")

    # نمایش گزینه‌ها
    for i, s in enumerate(sorted(scores, key=lambda x: x.total_score, reverse=True), 1):
        console.print(f"  [dim]{i}.[/dim] {s.model_name}/{s.format_name} (score: {s.total_score:.2f})")

    raw = Prompt.ask("Your favorites (comma-separated)", default="")
    favorites = [f.strip() for f in raw.split(",") if f.strip()] if raw else []

    feedback = Prompt.ask(
        "\n[cyan]Any feedback for the next round?[/cyan] [dim](optional)[/dim]",
        default="",
    )

    return favorites, feedback


def _show_winning_patterns() -> None:
    """نمایش الگوهای برنده از تاریخچه"""
    patterns = get_winning_patterns()
    if patterns["top_combos"]:
        console.print(Panel(
            f"[bold]Based on history:[/bold]\n"
            f"Best Model: [cyan]{patterns['best_model']}[/cyan]\n"
            f"Best Format: [magenta]{patterns['best_format']}[/magenta]\n"
            f"User Favorites: {patterns['user_favorites_count']} recorded",
            title="Optimization Insights",
            border_style="yellow",
        ))


def run_optimization(fal_key: str, anthropic_key: str) -> None:
    """
    اجرای حلقه اصلی بهینه‌سازی
    Run the main optimization loop
    """
    round_number = 1

    # نمایش تحلیل تاریخچه اگر وجود داشته باشد
    _show_winning_patterns()

    while True:
        console.print(Panel(
            f"[bold cyan]Optimization Round #{round_number}[/bold cyan]",
            border_style="cyan",
        ))

        # دریافت مفهوم طراحی از کاربر
        concept = Prompt.ask(
            "\n[bold]Enter your interior design concept[/bold]\n"
            "[dim]Example: minimalist Japanese bedroom with natural wood and soft lighting[/dim]\n"
            "Concept"
        )

        if not concept.strip():
            console.print("[yellow]No concept entered. Exiting.[/yellow]")
            break

        # انتخاب مدل‌ها
        selected_models = _select_models()

        # تولید فرمت‌های پرامپت
        console.print("\n[bold cyan]Step 1: Generating prompt format variations...[/bold cyan]")
        try:
            formats = generate_prompt_formats(concept, anthropic_key)
            display_prompt_formats(formats, concept)
        except Exception as e:
            console.print(f"[red]Failed to generate prompt formats: {e}[/red]")
            continue

        # تأیید کاربر قبل از تولید تصویر (هزینه‌بر)
        proceed = Confirm.ask(
            f"\nGenerate images for {len(formats)} formats × {len(selected_models)} models "
            f"= [bold]{len(formats) * len(selected_models)} images[/bold]?",
            default=True,
        )
        if not proceed:
            console.print("[yellow]Skipped image generation.[/yellow]")
            continue

        # تولید تصاویر
        console.print("\n[bold cyan]Step 2: Generating images...[/bold cyan]")
        generation_results = generate_images_for_formats(
            formats=formats,
            selected_models=selected_models,
            concept=concept,
            fal_key=fal_key,
        )

        display_generation_summary(generation_results)

        # ارزیابی تصاویر موفق با Claude Vision
        successful_results = [r for r in generation_results if r.success and r.image_path]

        if not successful_results:
            console.print("[red]No images generated successfully. Try again.[/red]")
            continue

        console.print(f"\n[bold cyan]Step 3: Evaluating {len(successful_results)} images with Claude Vision...[/bold cyan]")

        evaluation_scores = []
        for result in successful_results:
            console.print(f"  [dim]Evaluating {result.model_name}/{result.format_name}...[/dim]")
            score = evaluate_image(
                image_path=result.image_path,
                prompt_text=result.prompt_text,
                concept=concept,
                format_name=result.format_name,
                model_name=result.model_name,
                api_key=anthropic_key,
            )
            if score:
                evaluation_scores.append(score)

        if not evaluation_scores:
            console.print("[red]All evaluations failed.[/red]")
            continue

        # نمایش نتایج
        console.print("\n[bold cyan]Step 4: Results[/bold cyan]")
        display_evaluation_results(evaluation_scores)

        # دریافت نظر کاربر
        console.print("\n[bold cyan]Step 5: Your Feedback[/bold cyan]")
        favorites, feedback = _get_user_favorites(evaluation_scores)

        # ذخیره نتایج
        save_round_results(
            concept=concept,
            scores=evaluation_scores,
            user_favorites=favorites,
            user_feedback=feedback,
            round_number=round_number,
        )

        round_number += 1

        # ادامه یا پایان
        show_analytics = Confirm.ask("\nView cumulative analytics?", default=False)
        if show_analytics:
            display_analytics()

        another = Confirm.ask("\nRun another optimization round?", default=True)
        if not another:
            console.print(Panel(
                "[bold green]Optimization session complete![/bold green]\n"
                f"[dim]Completed {round_number - 1} round(s). Results saved to results/history.json[/dim]",
                border_style="green",
            ))
            break

        _show_winning_patterns()
