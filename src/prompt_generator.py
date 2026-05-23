"""
تولید کننده فرمت‌های مختلف پرامپت با استفاده از Claude API
Generates multiple structurally different prompt FORMAT variations using Claude
"""

import anthropic
import json
from typing import Dict
from rich.console import Console

from config import ANTHROPIC_MODEL, PROMPT_FORMATS

console = Console()


def generate_prompt_formats(concept: str, api_key: str) -> Dict[str, str]:
    """
    تولید ۶ فرمت مختلف پرامپت برای یک مفهوم طراحی داخلی
    Generate 6 different FORMAT variations for a given interior design concept.

    Returns a dict mapping format_name -> prompt_text
    """
    client = anthropic.Anthropic(api_key=api_key)

    system_prompt = """You are an expert interior design prompt engineer. Your task is to take
an interior design concept and generate 6 structurally DIFFERENT prompt formats for
AI image generation. Each format must have a genuinely different structure and approach
(not just different wording of the same format).

Return ONLY a valid JSON object with exactly these 6 keys and their prompt values:
- FORMAT_A: Simple Natural Language (1-2 sentences, conversational and clear)
- FORMAT_B: Detailed Descriptive Prose (3-4 sentences, rich descriptions flowing naturally)
- FORMAT_C: Keyword/Tag Style (comma-separated key terms, no full sentences, like: modern kitchen, marble countertops, pendant lighting, chef's island, warm oak cabinets)
- FORMAT_D: Technical/Structured (include explicit quality modifiers: photorealistic, 8K resolution, professional photography, architectural visualization, studio lighting)
- FORMAT_E: Style-First (begin with the architectural or artistic style, then describe the space: e.g., "Japandi minimalism meets..." or "Mid-century modern sanctuary with...")
- FORMAT_F: Atmosphere/Mood Focused (lead with sensory and emotional descriptors: how the space feels, smells, the quality of light, the emotions it evokes)

IMPORTANT: Return ONLY the JSON object, no markdown, no explanation, no extra text."""

    user_message = f"""Generate 6 different prompt formats for this interior design concept:

"{concept}"

Return the JSON object with FORMAT_A through FORMAT_F keys."""

    console.print("[dim]Generating prompt format variations with Claude...[/dim]")

    response = client.messages.create(
        model=ANTHROPIC_MODEL,
        max_tokens=2000,
        system=system_prompt,
        messages=[
            {"role": "user", "content": user_message}
        ]
    )

    # استخراج متن پاسخ
    response_text = response.content[0].text.strip()

    # پاک کردن کدبلاک‌های احتمالی markdown
    if response_text.startswith("```"):
        lines = response_text.split("\n")
        response_text = "\n".join(lines[1:-1])

    # پارس کردن JSON
    formats = json.loads(response_text)

    # اطمینان از وجود همه فرمت‌ها
    expected_keys = list(PROMPT_FORMATS.keys())
    for key in expected_keys:
        if key not in formats:
            formats[key] = f"Interior design: {concept}"

    return formats


def display_prompt_formats(formats: Dict[str, str], concept: str) -> None:
    """
    نمایش فرمت‌های پرامپت به شکل زیبا در ترمینال
    Display prompt formats beautifully in the terminal
    """
    from rich.panel import Panel
    from rich.table import Table
    from rich import box

    console.print(Panel(
        f"[bold cyan]Prompt Formats for: [white]{concept}[/white][/bold cyan]",
        border_style="cyan"
    ))

    format_descriptions = {
        "FORMAT_A": ("A", "Simple Natural Language"),
        "FORMAT_B": ("B", "Detailed Descriptive Prose"),
        "FORMAT_C": ("C", "Keyword/Tag Style"),
        "FORMAT_D": ("D", "Technical/Structured"),
        "FORMAT_E": ("E", "Style-First Approach"),
        "FORMAT_F": ("F", "Atmosphere/Mood Focused"),
    }

    for fmt_key, fmt_text in formats.items():
        letter, description = format_descriptions.get(fmt_key, (fmt_key, fmt_key))
        console.print(f"\n[bold magenta]FORMAT {letter}[/bold magenta] — [dim]{description}[/dim]")
        console.print(f"[white]{fmt_text}[/white]")
        console.print("[dim]" + "─" * 60 + "[/dim]")
