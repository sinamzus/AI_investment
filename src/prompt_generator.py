"""
تولید فرمت‌های مختلف پرامپت با استفاده از قالب‌های از پیش تعریف‌شده
Template-based prompt format generator — no external API needed
"""

from typing import Dict
from rich.console import Console
from rich.panel import Panel

console = Console()

# قالب‌های ثابت برای هر فرمت — {concept} با مفهوم کاربر جایگزین می‌شه
_TEMPLATES: Dict[str, str] = {
    "FORMAT_A": "{concept}",

    "FORMAT_B": (
        "A professionally designed interior space: {concept}. "
        "The room features carefully chosen furniture, balanced proportions, and harmonious color palette. "
        "Natural and artificial lighting work together to highlight key design elements. "
        "Photographed in the style of an architectural digest editorial."
    ),

    "FORMAT_C": (
        "{concept}, interior design, professional photography, "
        "high-end furniture, architectural details, ambient lighting, "
        "clean lines, carefully curated decor, lifestyle photography, "
        "magazine quality, realistic rendering"
    ),

    "FORMAT_D": (
        "{concept}, photorealistic, 8K resolution, ultra-detailed, "
        "architectural visualization, professional interior photography, "
        "studio lighting, sharp focus, high dynamic range, "
        "physically based rendering, octane render"
    ),

    "FORMAT_E": (
        "Contemporary architectural interior: {concept}. "
        "Inspired by award-winning interior design studios. "
        "Seamless blend of form and function, with thoughtful material choices "
        "and spatial flow that tells a cohesive design story."
    ),

    "FORMAT_F": (
        "Step inside: {concept}. "
        "The air carries a sense of calm and purpose. "
        "Warm light spills across textured surfaces, "
        "casting soft shadows that define the space. "
        "Every element feels intentional — a space that invites you to stay."
    ),
}

FORMAT_DESCRIPTIONS: Dict[str, str] = {
    "FORMAT_A": "Simple Natural Language",
    "FORMAT_B": "Detailed Descriptive Prose",
    "FORMAT_C": "Keyword / Tag Style",
    "FORMAT_D": "Technical + Quality Modifiers",
    "FORMAT_E": "Style-First / Architectural",
    "FORMAT_F": "Atmosphere / Mood Focused",
}


def generate_prompt_formats(concept: str) -> Dict[str, str]:
    """
    تولید ۶ فرمت پرامپت از روی قالب‌های ثابت
    Fill the 6 format templates with the user's concept
    """
    return {
        fmt_key: template.replace("{concept}", concept.strip())
        for fmt_key, template in _TEMPLATES.items()
    }


def display_prompt_formats(formats: Dict[str, str], concept: str) -> None:
    """نمایش فرمت‌های پرامپت در ترمینال"""
    console.print(Panel(
        f"[bold cyan]Prompt formats for:[/bold cyan] [white]{concept}[/white]",
        border_style="cyan",
    ))

    for fmt_key, prompt_text in formats.items():
        description = FORMAT_DESCRIPTIONS.get(fmt_key, fmt_key)
        console.print(f"\n[bold magenta]{fmt_key}[/bold magenta] — [dim]{description}[/dim]")
        console.print(f"[white]{prompt_text}[/white]")
        console.print("[dim]" + "─" * 60 + "[/dim]")
