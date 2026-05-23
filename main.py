"""
نقطه ورود اصلی سیستم بهینه‌سازی پرامپت طراحی داخلی
Main entry point for the Interior Design Prompt Optimization System
"""

import os
import sys
from pathlib import Path

# بارگذاری متغیرهای محیطی از فایل .env
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.text import Text
from rich.align import Align
from rich import box
from rich.rule import Rule

console = Console()

WELCOME_BANNER = """
 ██╗███╗   ██╗████████╗███████╗██████╗ ██╗ ██████╗ ██████╗
 ██║████╗  ██║╚══██╔══╝██╔════╝██╔══██╗██║██╔═══██╗██╔══██╗
 ██║██╔██╗ ██║   ██║   █████╗  ██████╔╝██║██║   ██║██████╔╝
 ██║██║╚██╗██║   ██║   ██╔══╝  ██╔══██╗██║██║   ██║██╔══██╗
 ██║██║ ╚████║   ██║   ███████╗██║  ██║██║╚██████╔╝██║  ██║
 ╚═╝╚═╝  ╚═══╝   ╚═╝   ╚══════╝╚═╝  ╚═╝╚═╝ ╚═════╝ ╚═╝  ╚═╝

   DESIGN PROMPT OPTIMIZER — Powered by Claude Vision + Fal.ai
"""


def display_welcome() -> None:
    """
    نمایش صفحه خوش‌آمدگویی زیبا
    Display the welcome screen with system explanation
    """
    console.print(Panel(
        Align.center(Text(WELCOME_BANNER, style="bold cyan")),
        border_style="cyan",
        padding=(1, 2),
    ))

    console.print(Panel(
        "[bold white]How this system works:[/bold white]\n\n"
        "  [cyan]1.[/cyan] You provide an [bold]interior design concept[/bold]\n"
        "  [cyan]2.[/cyan] Claude generates [bold]6 structurally different prompt formats[/bold]\n"
        "     (natural language, prose, keywords, technical, style-first, mood-focused)\n"
        "  [cyan]3.[/cyan] Each format is sent to [bold]multiple Fal.ai image models[/bold]\n"
        "     (Flux Pro, Flux Dev, Flux Realism, Stable Diffusion 3)\n"
        "  [cyan]4.[/cyan] [bold]Claude Vision[/bold] evaluates every image on 5 design criteria\n"
        "  [cyan]5.[/cyan] Results are ranked and you can [bold]pick your favorites[/bold]\n"
        "  [cyan]6.[/cyan] The system [bold]learns and refines[/bold] formats based on what worked\n\n"
        "[bold]Goal:[/bold] Find which prompt FORMAT works best for which MODEL for interior design.",
        title="[bold cyan]Interior Design Prompt Optimization System[/bold cyan]",
        border_style="cyan",
        padding=(1, 2),
    ))


def _get_api_key(env_var: str, display_name: str, prompt_text: str) -> str:
    """
    دریافت API key از محیط یا از کاربر
    Get API key from environment variable or prompt the user
    """
    key = os.environ.get(env_var, "").strip()
    if key:
        # نمایش بخشی از کلید برای تأیید
        masked = key[:8] + "..." + key[-4:] if len(key) > 12 else "***"
        console.print(f"[green]✓ {display_name} loaded from environment ({masked})[/green]")
        return key

    console.print(f"\n[yellow]{display_name} not found in environment.[/yellow]")
    console.print(f"[dim]Set {env_var} in your .env file or enter it now.[/dim]")

    key = Prompt.ask(
        f"[bold cyan]{prompt_text}[/bold cyan]",
        password=True,
    )

    if not key.strip():
        console.print(f"[red]Error: {display_name} cannot be empty.[/red]")
        sys.exit(1)

    return key.strip()


def _check_dependencies() -> bool:
    """
    بررسی نصب بودن وابستگی‌های لازم
    Check that all required packages are installed
    """
    missing = []
    packages = {
        "anthropic": "anthropic",
        "fal_client": "fal-client",
        "rich": "rich",
        "PIL": "Pillow",
        "aiohttp": "aiohttp",
        "dotenv": "python-dotenv",
    }

    for module, package in packages.items():
        try:
            __import__(module)
        except ImportError:
            missing.append(package)

    if missing:
        console.print(Panel(
            f"[red]Missing packages:[/red] {', '.join(missing)}\n\n"
            f"[yellow]Install with:[/yellow]\n"
            f"[bold]pip install {' '.join(missing)}[/bold]",
            title="[red]Dependency Error[/red]",
            border_style="red",
        ))
        return False

    return True


def _ensure_results_dir() -> None:
    """اطمینان از وجود پوشه نتایج"""
    results_dir = Path(__file__).parent / "results"
    results_dir.mkdir(parents=True, exist_ok=True)


def main() -> None:
    """
    تابع اصلی — نقطه شروع برنامه
    Main function — application entry point
    """
    # نمایش خوش‌آمدگویی
    display_welcome()

    # بررسی وابستگی‌ها
    console.print(Rule("[dim]System Check[/dim]"))
    if not _check_dependencies():
        sys.exit(1)
    console.print("[green]✓ All dependencies installed[/green]")

    # اطمینان از وجود پوشه نتایج
    _ensure_results_dir()
    console.print("[green]✓ Results directory ready[/green]")

    # ── دریافت API Keys ────────────────────────────────────────────────────
    console.print(Rule("[dim]API Configuration[/dim]"))

    fal_key = _get_api_key(
        env_var="FAL_KEY",
        display_name="Fal.ai API Key",
        prompt_text="Enter your FAL_KEY",
    )

    anthropic_key = _get_api_key(
        env_var="ANTHROPIC_API_KEY",
        display_name="Anthropic API Key",
        prompt_text="Enter your ANTHROPIC_API_KEY",
    )

    # ── تست اتصال سریع ────────────────────────────────────────────────────
    console.print(Rule("[dim]Starting Optimization[/dim]"))
    console.print(
        "\n[bold cyan]System ready![/bold cyan] "
        "Starting the interior design prompt optimization loop...\n"
    )

    # ── اجرای حلقه اصلی بهینه‌سازی ──────────────────────────────────────
    try:
        from src.optimizer import run_optimization_loop
        run_optimization_loop(fal_key=fal_key, anthropic_key=anthropic_key)
    except KeyboardInterrupt:
        console.print("\n\n[yellow]Session interrupted by user.[/yellow]")
        console.print("[dim]Your results have been saved to results/history.json[/dim]")
    except Exception as e:
        console.print(Panel(
            f"[red]Unexpected error:[/red] {e}\n\n"
            "[dim]Check your API keys and network connection.[/dim]",
            title="[red]Error[/red]",
            border_style="red",
        ))
        raise

    # ── پایان ─────────────────────────────────────────────────────────────
    console.print(Panel(
        "[bold cyan]Thank you for using the Interior Design Prompt Optimizer![/bold cyan]\n"
        "[dim]Results saved to: results/history.json[/dim]\n"
        "[dim]Generated images saved in: results/[/dim]",
        border_style="cyan",
        padding=(1, 2),
    ))


if __name__ == "__main__":
    main()
