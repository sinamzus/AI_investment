"""
سیستم بهینه‌سازی پرامپت طراحی داخلی
Interior Design AI Image Generation Prompt Optimizer

یافتن بهترین فرمت پرامپت برای هر مدل تولید تصویر در زمینه طراحی داخلی
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt

# بارگذاری متغیرهای محیطی از فایل .env
load_dotenv()

console = Console()

WELCOME_TEXT = """
[bold cyan]Interior Design Prompt Optimizer[/bold cyan]

This system helps you discover the [bold]best prompt format[/bold] for AI image
generation models in the field of [bold]interior design[/bold].

How it works:
  [magenta]1.[/magenta] You provide an interior design concept
  [magenta]2.[/magenta] Claude generates 6 structurally different prompt formats
  [magenta]3.[/magenta] Images are generated using selected Fal.ai models
  [magenta]4.[/magenta] Claude Vision evaluates each result on 5 criteria
  [magenta]5.[/magenta] You provide feedback to guide future optimization
  [magenta]6.[/magenta] Over time, the system identifies which formats work best

[dim]Prompt formats tested: Simple | Prose | Keywords | Technical | Style-First | Mood[/dim]
[dim]Models available: flux-pro | flux-dev | flux-realism | sd3[/dim]
"""


def get_api_keys() -> tuple[str, str]:
    """دریافت API Key‌ها از محیط یا کاربر"""
    fal_key = os.environ.get("FAL_KEY", "")
    anthropic_key = os.environ.get("ANTHROPIC_API_KEY", "")

    if not fal_key:
        console.print("\n[yellow]FAL_KEY not found in environment.[/yellow]")
        fal_key = Prompt.ask("[cyan]Enter your Fal.ai API key[/cyan]", password=True)

    if not anthropic_key:
        console.print("\n[yellow]ANTHROPIC_API_KEY not found in environment.[/yellow]")
        anthropic_key = Prompt.ask("[cyan]Enter your Anthropic API key[/cyan]", password=True)

    if not fal_key or not anthropic_key:
        console.print("[red]Both API keys are required. Exiting.[/red]")
        sys.exit(1)

    return fal_key, anthropic_key


def check_dependencies() -> bool:
    """بررسی نصب بودن وابستگی‌های لازم"""
    missing = []

    try:
        import fal_client
    except ImportError:
        missing.append("fal-client")

    try:
        import anthropic
    except ImportError:
        missing.append("anthropic")

    try:
        import rich
    except ImportError:
        missing.append("rich")

    try:
        import dotenv
    except ImportError:
        missing.append("python-dotenv")

    if missing:
        console.print(Panel(
            f"[red]Missing required packages:[/red] {', '.join(missing)}\n\n"
            "[yellow]Install with:[/yellow]\n"
            f"[bold]pip install {' '.join(missing)}[/bold]\n\n"
            "Or install all dependencies:\n"
            "[bold]pip install -r requirements.txt[/bold]",
            title="Missing Dependencies",
            border_style="red",
        ))
        return False

    return True


def main():
    """نقطه ورود اصلی برنامه"""
    console.print(Panel(WELCOME_TEXT, border_style="cyan", padding=(1, 2)))

    if not check_dependencies():
        sys.exit(1)

    fal_key, anthropic_key = get_api_keys()

    console.print("\n[green]✓ API keys loaded successfully[/green]")
    console.print("[dim]Starting optimization system...[/dim]\n")

    # اجرای حلقه بهینه‌سازی
    from src.optimizer import run_optimization
    run_optimization(fal_key=fal_key, anthropic_key=anthropic_key)


if __name__ == "__main__":
    main()
