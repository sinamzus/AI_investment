"""
سیستم بهینه‌سازی پرامپت طراحی داخلی — فقط با FAL_KEY
Interior Design Prompt Optimizer — FAL_KEY only
"""

import os
import sys

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.rule import Rule

console = Console()

BANNER = """
  ██████╗ ██████╗  ██████╗ ███╗   ███╗██████╗ ████████╗
  ██╔══██╗██╔══██╗██╔═══██╗████╗ ████║██╔══██╗╚══██╔══╝
  ██████╔╝██████╔╝██║   ██║██╔████╔██║██████╔╝   ██║
  ██╔═══╝ ██╔══██╗██║   ██║██║╚██╔╝██║██╔═══╝    ██║
  ██║     ██║  ██║╚██████╔╝██║ ╚═╝ ██║██║        ██║
  ╚═╝     ╚═╝  ╚═╝ ╚═════╝ ╚═╝     ╚═╝╚═╝        ╚═╝
        Interior Design Prompt Optimizer — Fal.ai
"""


def main() -> None:
    console.print(Panel(BANNER, border_style="cyan", padding=(0, 2)))

    console.print(Panel(
        "[bold white]How it works:[/bold white]\n\n"
        "  [cyan]1.[/cyan] You enter an interior design concept\n"
        "  [cyan]2.[/cyan] 6 structurally different prompt formats are generated\n"
        "  [cyan]3.[/cyan] Images are generated via selected Fal.ai models\n"
        "  [cyan]4.[/cyan] You view each image URL and rate it 1–10\n"
        "  [cyan]5.[/cyan] The system tracks which format+model combos win over time\n\n"
        "[dim]Formats: Simple | Prose | Keywords | Technical | Style-First | Mood[/dim]\n"
        "[dim]Models:  flux-pro | flux-dev | flux-realism | sd3[/dim]",
        title="[bold cyan]Interior Design Prompt Optimizer[/bold cyan]",
        border_style="cyan",
        padding=(1, 2),
    ))

    console.print(Rule("[dim]Setup[/dim]"))

    # ── FAL_KEY ───────────────────────────────────────────────────────────
    fal_key = os.environ.get("FAL_KEY", "").strip()
    if fal_key:
        masked = fal_key[:8] + "..." + fal_key[-4:]
        console.print(f"[green]✓ FAL_KEY loaded ({masked})[/green]")
    else:
        fal_key = Prompt.ask("[bold cyan]Enter your FAL_KEY[/bold cyan]", password=True)
        if not fal_key.strip():
            console.print("[red]FAL_KEY is required. Exiting.[/red]")
            sys.exit(1)

    console.print(Rule("[dim]Starting[/dim]"))

    try:
        from src.optimizer import run_optimization_loop
        run_optimization_loop(fal_key=fal_key)
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted. Results saved.[/yellow]")


if __name__ == "__main__":
    main()
