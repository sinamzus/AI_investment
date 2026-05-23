"""
حلقه اصلی بهینه‌سازی پرامپت طراحی داخلی
Main optimization loop orchestrating the full workflow
"""

import json
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import anthropic
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm, IntPrompt
from rich.table import Table
from rich import box

from config import (
    FAL_MODELS,
    ANTHROPIC_MODEL,
    PROMPT_FORMATS,
)
from src.prompt_generator import generate_prompt_formats, display_prompt_formats
from src.image_generator import generate_images_for_formats, display_generation_summary
from src.evaluator import (
    EvaluationScore,
    evaluate_image,
    display_evaluation_results,
)
from src.results_tracker import ResultsTracker

console = Console()


def _select_models() -> List[str]:
    """
    درخواست از کاربر برای انتخاب مدل‌های تولید تصویر
    Ask user which Fal.ai models to use (default: flux-pro + flux-dev)
    """
    console.print("\n[bold cyan]Available Fal.ai Models:[/bold cyan]")
    model_list = list(FAL_MODELS.keys())
    for i, model in enumerate(model_list, 1):
        console.print(f"  [magenta]{i}.[/magenta] {model}  [dim]({FAL_MODELS[model]})[/dim]")

    console.print("\n[dim]Enter model numbers separated by commas (e.g., 1,2) or press Enter for default (flux-pro + flux-dev)[/dim]")
    selection = Prompt.ask("[cyan]Your selection[/cyan]", default="1,2")

    selected = []
    try:
        indices = [int(x.strip()) for x in selection.split(",") if x.strip()]
        for idx in indices:
            if 1 <= idx <= len(model_list):
                selected.append(model_list[idx - 1])
    except ValueError:
        pass

    if not selected:
        selected = ["flux-pro", "flux-dev"]
        console.print("[dim]Using default: flux-pro + flux-dev[/dim]")

    console.print(f"[green]Selected models: {', '.join(selected)}[/green]")
    return selected


def _get_user_ratings(sorted_scores: List[EvaluationScore]) -> Tuple[Dict[str, int], str, Optional[str]]:
    """
    دریافت امتیاز کاربر و بازخورد متنی
    Ask user to rate their favorites and provide feedback

    Returns: (ratings_dict, feedback_text, favorite_key)
    """
    console.print("\n[bold cyan]Your Turn — Rate the Results[/bold cyan]")
    console.print("[dim]Enter the rank numbers of your favorites (e.g., 1,2) and optional feedback.[/dim]\n")

    # نمایش گزینه‌های رتبه‌بندی
    for i, score in enumerate(sorted_scores, 1):
        color = "green" if score.total_score >= 7 else "yellow" if score.total_score >= 5 else "red"
        console.print(
            f"  [bold]{i}.[/bold] {score.model_name}/{score.format_name} "
            f"— [{color}]{score.total_score:.2f}/10[/{color}]"
        )

    # درخواست انتخاب مورد علاقه
    favorite_input = Prompt.ask(
        "\n[cyan]Which result(s) do you like best? (rank numbers, e.g., 1 or 1,2)[/cyan]",
        default="1"
    )

    # پردازش ورودی کاربر
    ratings: Dict[str, int] = {}
    favorite_key = None
    try:
        fav_indices = [int(x.strip()) for x in favorite_input.split(",") if x.strip()]
        for rank_idx in fav_indices:
            if 1 <= rank_idx <= len(sorted_scores):
                chosen = sorted_scores[rank_idx - 1]
                key = f"{chosen.format_name}_{chosen.model_name}"
                ratings[key] = 5  # امتیاز کاربر به مورد علاقه
                if favorite_key is None:
                    favorite_key = key
        # امتیاز کمتر به بقیه
        for i, score in enumerate(sorted_scores, 1):
            key = f"{score.format_name}_{score.model_name}"
            if key not in ratings:
                ratings[key] = max(1, 5 - i)
    except ValueError:
        # در صورت خطا، اولین نتیجه را به عنوان مورد علاقه در نظر می‌گیریم
        if sorted_scores:
            chosen = sorted_scores[0]
            favorite_key = f"{chosen.format_name}_{chosen.model_name}"
            ratings[favorite_key] = 5

    # درخواست بازخورد متنی
    feedback = Prompt.ask(
        "[cyan]Any feedback? What did you like or dislike?[/cyan] (press Enter to skip)",
        default=""
    )
    if not feedback:
        feedback = "No specific feedback provided."

    return ratings, feedback, favorite_key


def _analyze_winning_patterns(
    sorted_scores: List[EvaluationScore],
    tracker: ResultsTracker,
) -> Dict:
    """
    تحلیل الگوهای برنده برای بهینه‌سازی بعدی
    Analyze which format+model combos perform best
    """
    analytics = tracker.get_analytics()

    patterns = {
        "current_winner_model": sorted_scores[0].model_name if sorted_scores else None,
        "current_winner_format": sorted_scores[0].format_name if sorted_scores else None,
        "current_winner_score": sorted_scores[0].total_score if sorted_scores else 0,
        "historical_best_model": analytics.get("best_model_overall", {}).get("model"),
        "historical_best_format": analytics.get("best_format_overall", {}).get("format"),
        "top_combinations": analytics.get("top_combinations", []),
    }

    return patterns


def _generate_refined_formats(
    concept: str,
    winning_score: EvaluationScore,
    user_feedback: str,
    api_key: str,
    iteration: int,
) -> Dict[str, str]:
    """
    تولید فرمت‌های بهینه‌شده بر اساس برنده قبلی و بازخورد کاربر
    Generate refined prompt formats based on the winning pattern and user feedback
    """
    client = anthropic.Anthropic(api_key=api_key)

    system_prompt = """You are an expert interior design prompt engineer optimizing AI image generation prompts.

Based on a winning prompt and user feedback, generate 6 refined FORMAT variations.
Each format must be structurally distinct (same concept as before: A=simple, B=prose, C=keywords, D=technical, E=style-first, F=mood).

Return ONLY a valid JSON object with FORMAT_A through FORMAT_F keys and their prompt values.
No markdown, no explanation — just the JSON."""

    user_message = f"""Optimization Round {iteration}

ORIGINAL CONCEPT: "{concept}"

BEST PERFORMING PROMPT (from previous round):
Format Type: {winning_score.format_name}
Model: {winning_score.model_name}
Score: {winning_score.total_score:.2f}/10
Prompt: "{winning_score.prompt_text}"

USER FEEDBACK: "{user_feedback}"

Now generate 6 refined FORMAT variations (FORMAT_A through FORMAT_F) for this concept,
incorporating lessons from what worked. Keep structural differences between formats.
Return ONLY the JSON object."""

    response = client.messages.create(
        model=ANTHROPIC_MODEL,
        max_tokens=2000,
        system=system_prompt,
        messages=[{"role": "user", "content": user_message}],
    )

    response_text = response.content[0].text.strip()
    if response_text.startswith("```"):
        lines = response_text.split("\n")
        response_text = "\n".join(lines[1:-1])

    refined_formats = json.loads(response_text)

    # اطمینان از وجود همه فرمت‌ها
    for key in PROMPT_FORMATS:
        if key not in refined_formats:
            refined_formats[key] = f"Interior design: {concept}"

    return refined_formats


def run_optimization_loop(fal_key: str, anthropic_key: str) -> None:
    """
    حلقه اصلی بهینه‌سازی — نقطه ورود اصلی برای فرایند بهینه‌سازی
    Main optimization loop — the core workflow

    Orchestrates:
    1. Concept input
    2. Format generation
    3. Model selection
    4. Image generation
    5. Claude Vision evaluation
    6. User feedback
    7. Pattern analysis
    8. Iterative refinement
    """
    tracker = ResultsTracker()
    session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    iteration = 1
    current_formats: Optional[Dict[str, str]] = None
    last_winning_score: Optional[EvaluationScore] = None
    last_feedback: str = ""
    concept: str = ""

    # نمایش تاریخچه در صورت وجود
    if tracker.history:
        show_history = Confirm.ask(
            f"\n[cyan]Found {len(tracker.history)} historical records. Show summary?[/cyan]",
            default=False
        )
        if show_history:
            tracker.generate_summary_report()

    # ─── حلقه اصلی ───────────────────────────────────────────────────────────
    while True:
        console.print(Panel(
            f"[bold cyan]OPTIMIZATION ROUND {iteration}[/bold cyan]",
            border_style="cyan",
            expand=False,
        ))

        # ── مرحله ۱: دریافت مفهوم از کاربر ──────────────────────────────────
        if iteration == 1 or Confirm.ask("\n[cyan]Use a new concept?[/cyan]", default=True):
            concept = Prompt.ask(
                "[bold cyan]Enter your interior design concept[/bold cyan]",
                default="A modern minimalist living room with warm lighting and natural materials",
            )
        else:
            console.print(f"[dim]Continuing with concept: {concept}[/dim]")

        # ── مرحله ۲: تولید فرمت‌های پرامپت ──────────────────────────────────
        console.print(f"\n[cyan]Generating prompt formats...[/cyan]")

        try:
            if iteration == 1 or current_formats is None:
                # دور اول: تولید فرمت‌های پایه
                current_formats = generate_prompt_formats(concept, anthropic_key)
            else:
                # دورهای بعدی: بهینه‌سازی بر اساس برنده قبلی
                if last_winning_score and Confirm.ask(
                    "\n[cyan]Refine formats based on last winning prompt?[/cyan]",
                    default=True,
                ):
                    console.print("[dim]Generating refined formats based on winning pattern...[/dim]")
                    current_formats = _generate_refined_formats(
                        concept=concept,
                        winning_score=last_winning_score,
                        user_feedback=last_feedback,
                        api_key=anthropic_key,
                        iteration=iteration,
                    )
                else:
                    current_formats = generate_prompt_formats(concept, anthropic_key)

        except Exception as e:
            console.print(f"[red]Failed to generate formats: {e}[/red]")
            if Confirm.ask("[yellow]Retry?[/yellow]", default=True):
                continue
            break

        display_prompt_formats(current_formats, concept)

        # ── مرحله ۳: انتخاب مدل‌ها ───────────────────────────────────────────
        selected_models = _select_models()

        # ── مرحله ۴: تولید تصاویر ────────────────────────────────────────────
        console.print(f"\n[bold cyan]Starting image generation...[/bold cyan]")

        try:
            generation_results = generate_images_for_formats(
                formats=current_formats,
                selected_models=selected_models,
                concept=concept,
                fal_key=fal_key,
            )
        except Exception as e:
            console.print(f"[red]Image generation failed: {e}[/red]")
            if Confirm.ask("[yellow]Retry generation?[/yellow]", default=True):
                continue
            break

        display_generation_summary(generation_results)

        # بررسی موفقیت حداقل یک تصویر
        successful_gens = [r for r in generation_results if r.success and r.image_path]
        if not successful_gens:
            console.print("[red]No images were generated successfully. Cannot evaluate.[/red]")
            if Confirm.ask("[yellow]Try again?[/yellow]", default=True):
                continue
            break

        # ── مرحله ۵: ارزیابی با Claude Vision ───────────────────────────────
        console.print(f"\n[bold cyan]Evaluating images with Claude Vision...[/bold cyan]")

        evaluation_scores: List[EvaluationScore] = []
        for gen_result in successful_gens:
            console.print(
                f"  [dim]Evaluating {gen_result.model_name}/{gen_result.format_name}...[/dim]",
                end="",
            )
            try:
                score = evaluate_image(
                    image_path=gen_result.image_path,
                    prompt_text=gen_result.prompt_text,
                    concept=concept,
                    format_name=gen_result.format_name,
                    model_name=gen_result.model_name,
                    api_key=anthropic_key,
                )
                if score:
                    evaluation_scores.append(score)
                    color = "green" if score.total_score >= 7 else "yellow" if score.total_score >= 5 else "red"
                    console.print(f" [{color}]{score.total_score:.2f}/10[/{color}]")
                else:
                    console.print(" [red]failed[/red]")
            except Exception as e:
                console.print(f" [red]error: {e}[/red]")
            # تأخیر کوچک برای جلوگیری از rate limiting
            time.sleep(0.3)

        if not evaluation_scores:
            console.print("[red]No evaluations completed.[/red]")
            if Confirm.ask("[yellow]Continue anyway?[/yellow]", default=False):
                continue
            break

        # ── مرحله ۶: نمایش نتایج رتبه‌بندی‌شده ─────────────────────────────
        console.print(f"\n[bold cyan]Results Ranking[/bold cyan]")
        sorted_scores = sorted(evaluation_scores, key=lambda s: s.total_score, reverse=True)
        display_evaluation_results(sorted_scores)

        # نمایش توضیح برنده برتر
        if sorted_scores:
            top = sorted_scores[0]
            console.print(Panel(
                f"[bold]Prompt:[/bold] [italic]{top.prompt_text}[/italic]\n\n"
                f"[bold]Claude's Analysis:[/bold] [dim]{top.reasoning}[/dim]",
                title=f"[bold green]Winner: {top.model_name} + {top.format_name} — {top.total_score:.2f}/10[/bold green]",
                border_style="green",
            ))

        # ── مرحله ۷: دریافت بازخورد کاربر ───────────────────────────────────
        user_ratings, user_feedback, favorite_key = _get_user_ratings(sorted_scores)
        last_feedback = user_feedback

        # تعیین برنده بر اساس انتخاب کاربر
        if favorite_key:
            # پیدا کردن بهترین نتیجه انتخاب‌شده توسط کاربر
            # کلید به فرم "FORMAT_A_flux-pro" است؛ مقایسه مستقیم با هر نتیجه
            user_winner = next(
                (s for s in sorted_scores
                 if f"{s.format_name}_{s.model_name}" == favorite_key),
                sorted_scores[0] if sorted_scores else None,
            )
            if user_winner:
                last_winning_score = user_winner
                console.print(
                    f"\n[green]Your favorite: {user_winner.model_name}/{user_winner.format_name} "
                    f"({user_winner.total_score:.2f}/10)[/green]"
                )
        else:
            last_winning_score = sorted_scores[0] if sorted_scores else None

        # ── مرحله ۸: ذخیره نتایج ────────────────────────────────────────────
        console.print("\n[dim]Saving results to history...[/dim]")

        for score in evaluation_scores:
            key = f"{score.format_name}_{score.model_name}"
            scores_dict = {
                "design_coherence": score.design_coherence,
                "interior_quality": score.interior_quality,
                "aesthetic_appeal": score.aesthetic_appeal,
                "technical_quality": score.technical_quality,
                "usability": score.usability,
                "total": score.total_score,
            }
            from config import PROMPT_FORMATS as PF
            tracker.add_result(
                concept=concept,
                format_type=score.format_name,
                format_name=PF.get(score.format_name, score.format_name),
                prompt_text=score.prompt_text,
                model=score.model_name,
                image_path=score.image_path,
                scores=scores_dict,
                user_rating=user_ratings.get(key),
                user_feedback=user_feedback if user_ratings.get(key) == 5 else None,
                iteration=iteration,
                session_id=session_id,
            )

        # ── مرحله ۹: تحلیل الگوها ───────────────────────────────────────────
        patterns = _analyze_winning_patterns(sorted_scores, tracker)
        console.print(Panel(
            f"[cyan]Current Round Winner:[/cyan] {patterns['current_winner_model']}/{patterns['current_winner_format']} "
            f"({patterns['current_winner_score']:.2f}/10)\n"
            + (f"[dim]Historical Best Model: {patterns['historical_best_model']}[/dim]\n"
               f"[dim]Historical Best Format: {patterns['historical_best_format']}[/dim]"
               if patterns["historical_best_model"] else ""),
            title="Pattern Analysis",
            border_style="magenta",
        ))

        # ── مرحله ۱۰: ادامه یا پایان ────────────────────────────────────────
        iteration += 1
        console.print()

        if not Confirm.ask(
            f"[bold cyan]Run another optimization iteration (Round {iteration})?[/bold cyan]",
            default=True,
        ):
            break

    # ── گزارش نهایی ──────────────────────────────────────────────────────────
    console.print(Panel(
        "[bold cyan]Session Complete[/bold cyan]\n"
        f"Completed {iteration - 1} optimization round(s).",
        border_style="cyan",
    ))

    if Confirm.ask("\n[cyan]Show full optimization history summary?[/cyan]", default=True):
        tracker.generate_summary_report()
