"""Terminal rendering using Rich."""
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

console = Console()


def show_report(summoner: str, report: str) -> None:
    console.print(
        Panel(
            Markdown(report),
            title=f"[bold cyan]Coaching Report — {summoner}[/bold cyan]",
            border_style="cyan",
            padding=(1, 2),
        )
    )


def show_error(message: str) -> None:
    console.print(f"[bold red]Error:[/bold red] {message}")


def show_progress(message: str) -> None:
    console.print(f"[dim]{message}[/dim]")
