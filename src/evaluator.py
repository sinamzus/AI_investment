"""
ارزیابی تصاویر طراحی داخلی با استفاده از Claude Vision
Evaluate interior design images using Claude Vision
"""

import anthropic
import base64
import json
from pathlib import Path
from typing import Optional
from dataclasses import dataclass
from rich.console import Console

from config import ANTHROPIC_MODEL, EVALUATION_CRITERIA

console = Console()


@dataclass
class EvaluationScore:
    """نتیجه ارزیابی یک تصویر"""
    format_name: str
    model_name: str
    prompt_text: str
    image_path: str
    design_coherence: float
    interior_quality: float
    aesthetic_appeal: float
    technical_quality: float
    usability: float
    total_score: float
    reasoning: str
    concept: str


def _encode_image(image_path: str) -> str:
    """تبدیل تصویر به base64 برای ارسال به Claude"""
    with open(image_path, "rb") as f:
        return base64.standard_b64encode(f.read()).decode("utf-8")


def evaluate_image(
    image_path: str,
    prompt_text: str,
    concept: str,
    format_name: str,
    model_name: str,
    api_key: str,
) -> Optional[EvaluationScore]:
    """
    ارزیابی یک تصویر طراحی داخلی با Claude Vision
    Evaluate a single interior design image using Claude Vision
    """
    client = anthropic.Anthropic(api_key=api_key)

    try:
        image_data = _encode_image(image_path)
    except Exception as e:
        console.print(f"[red]Failed to read image {image_path}: {e}[/red]")
        return None

    evaluation_prompt = f"""You are an expert interior design critic and AI image evaluation specialist.

Evaluate this AI-generated interior design image against the following concept and prompt.

Original Concept: "{concept}"
Prompt Used ({format_name}): "{prompt_text}"

Score each criterion from 0 to 10:

1. Design Coherence (0-10): How well does the image match the stated concept and prompt?
2. Interior Design Quality (0-10): Professionalism, realistic proportions, proper furniture arrangement, spatial awareness?
3. Aesthetic Appeal (0-10): Is the composition beautiful and visually pleasing?
4. Technical Quality (0-10): Lighting quality, detail level, photorealism, rendering quality?
5. Usability (0-10): Would a real client approve this? Is it practical and inspiring?

Return ONLY a valid JSON object with this exact structure:
{{
  "design_coherence": <number 0-10>,
  "interior_quality": <number 0-10>,
  "aesthetic_appeal": <number 0-10>,
  "technical_quality": <number 0-10>,
  "usability": <number 0-10>,
  "reasoning": "<brief 2-3 sentence explanation of scores and what works/doesn't work>"
}}

Return ONLY the JSON. No markdown, no explanation, just the JSON object."""

    try:
        response = client.messages.create(
            model=ANTHROPIC_MODEL,
            max_tokens=500,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/png",
                                "data": image_data,
                            },
                        },
                        {
                            "type": "text",
                            "text": evaluation_prompt,
                        },
                    ],
                }
            ],
        )

        response_text = response.content[0].text.strip()

        # پاک کردن markdown احتمالی
        if response_text.startswith("```"):
            lines = response_text.split("\n")
            response_text = "\n".join(lines[1:-1])

        scores = json.loads(response_text)

        total = (
            scores["design_coherence"]
            + scores["interior_quality"]
            + scores["aesthetic_appeal"]
            + scores["technical_quality"]
            + scores["usability"]
        ) / 5.0

        return EvaluationScore(
            format_name=format_name,
            model_name=model_name,
            prompt_text=prompt_text,
            image_path=image_path,
            design_coherence=scores["design_coherence"],
            interior_quality=scores["interior_quality"],
            aesthetic_appeal=scores["aesthetic_appeal"],
            technical_quality=scores["technical_quality"],
            usability=scores["usability"],
            total_score=round(total, 2),
            reasoning=scores["reasoning"],
            concept=concept,
        )

    except Exception as e:
        console.print(f"[red]Evaluation failed for {format_name}/{model_name}: {e}[/red]")
        return None


def display_evaluation_results(scores: list[EvaluationScore]) -> None:
    """نمایش نتایج ارزیابی به صورت جدول رتبه‌بندی‌شده"""
    from rich.table import Table
    from rich.panel import Panel
    from rich import box

    sorted_scores = sorted(scores, key=lambda s: s.total_score, reverse=True)

    table = Table(
        title="Evaluation Results — Ranked by Total Score",
        box=box.ROUNDED,
        border_style="cyan",
        show_lines=True,
    )

    table.add_column("Rank", justify="center", style="bold")
    table.add_column("Model", style="cyan", no_wrap=True)
    table.add_column("Format", style="magenta")
    table.add_column("Coherence", justify="center")
    table.add_column("Quality", justify="center")
    table.add_column("Aesthetics", justify="center")
    table.add_column("Technical", justify="center")
    table.add_column("Usability", justify="center")
    table.add_column("TOTAL", justify="center", style="bold yellow")

    for i, s in enumerate(sorted_scores, 1):
        rank_style = {1: "gold1", 2: "silver", 3: "dark_orange"}.get(i, "white")
        rank = f"[{rank_style}]#{i}[/{rank_style}]"

        def fmt(v):
            color = "green" if v >= 7 else "yellow" if v >= 5 else "red"
            return f"[{color}]{v:.1f}[/{color}]"

        total_color = "green" if s.total_score >= 7 else "yellow" if s.total_score >= 5 else "red"

        table.add_row(
            rank,
            s.model_name,
            s.format_name,
            fmt(s.design_coherence),
            fmt(s.interior_quality),
            fmt(s.aesthetic_appeal),
            fmt(s.technical_quality),
            fmt(s.usability),
            f"[bold {total_color}]{s.total_score:.2f}[/bold {total_color}]",
        )

    console.print(table)

    # نمایش توضیحات برنده
    if sorted_scores:
        best = sorted_scores[0]
        console.print(Panel(
            f"[bold yellow]Winner: {best.model_name} + {best.format_name} (Score: {best.total_score:.2f}/10)[/bold yellow]\n"
            f"[dim]{best.reasoning}[/dim]",
            title="Best Result",
            border_style="yellow",
        ))
