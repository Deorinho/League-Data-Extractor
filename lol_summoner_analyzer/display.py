"""Terminal rendering using Rich."""
from __future__ import annotations

import datetime
from pathlib import Path
from typing import TYPE_CHECKING

from rich.align import Align
from rich.console import Console
from rich.markdown import Markdown
from rich.markup import escape
from rich.panel import Panel
from rich.progress import BarColumn, MofNCompleteColumn, Progress, TextColumn
from rich.rule import Rule
from rich.text import Text

if TYPE_CHECKING:
    from lol_summoner_analyzer.fetchers.riot import RankInfo

# ── Colour palette ────────────────────────────────────────────────────────────
# Change any hex value here to restyle the whole CLI.
C_GOLD        = "#FFD700"   # Golden yellow  — borders, titles, tier name
C_BLUE        = "#4169E1"   # Royal blue     — labels, progress text
C_TEAL        = "#0D9488"   # Dark teal      — rules, accent lines
C_ERROR       = "#FF4C4C"   # Red            — error message body
C_BAR_FILL    = "#FFD700"   # Golden yellow  — filled division pip  ██
C_BAR_EMPTY   = "#1E3A5F"   # Deep navy      — empty division pip   ░░
C_STAT        = "#CBD5E1"   # Light slate    — secondary stat text
# ─────────────────────────────────────────────────────────────────────────────

# Legacy aliases kept so existing call-sites don't change.
C_BORDER      = C_GOLD
C_TITLE       = C_GOLD
C_LABEL       = C_BLUE
C_ERROR_MSG   = C_ERROR
C_PROGRESS    = C_BLUE
C_HEADER_RULE = C_TEAL

console = Console()

# Each division maps to how many of the 4 pips are filled.
# IV → leftmost pip only; I → all four pips filled.
_DIVISION_FILL: dict[str, int] = {"IV": 1, "III": 2, "II": 3, "I": 4}


def show_banner() -> None:
    """Print the startup header — call once at the top of the CLI command."""
    console.print()
    console.print(Rule(
        f"[bold {C_GOLD}]⚔  League Stats Analyzer  ⚔[/bold {C_GOLD}]",
        style=C_TEAL,
    ))
    console.print()


def show_rank_panel(rank_info: RankInfo | None) -> None:
    """Render a rank panel with tier name, LP, win-rate and a division progress bar."""
    if rank_info is None:
        console.print(f"[{C_BLUE}]  ›  Rank: Unranked[/{C_BLUE}]")
        return

    fill  = _DIVISION_FILL.get(rank_info.division, 0)
    total = rank_info.wins + rank_info.losses
    wr    = round(rank_info.wins / total * 100) if total else 0

    # Build the progress bar — 2 block chars per division level = 8 chars wide
    bar = Text()
    bar.append("██" * fill,        style=C_BAR_FILL)
    bar.append("░░" * (4 - fill),  style=C_BAR_EMPTY)

    content = Text(justify="center")
    content.append(f"{rank_info.tier.upper()}  ", style=f"bold {C_GOLD}")
    content.append_text(bar)
    content.append(f"  Division {rank_info.division}\n", style=C_STAT)
    content.append(
        f"{rank_info.lp} LP   ·   {rank_info.wins}W / {rank_info.losses}L   ·   {wr}% WR",
        style=C_STAT,
    )

    console.print(Panel(
        Align.center(content),
        border_style=C_TEAL,
        padding=(0, 4),
    ))


def make_fetch_progress() -> Progress:
    """Return a styled progress bar for the match-fetching loop."""
    return Progress(
        TextColumn(f"[{C_BLUE}]  ›  {{task.description}}[/{C_BLUE}]"),
        BarColumn(
            bar_width=24,
            style=C_BAR_EMPTY,
            complete_style=C_BAR_FILL,
            finished_style=C_GOLD,
        ),
        MofNCompleteColumn(),
        console=console,
        transient=False,
    )


def show_report(summoner: str, report: str) -> None:
    console.print()
    console.print(Rule(style=C_TEAL))
    console.print(Panel(
        Markdown(report),
        title=Text(f"Coaching Report — {summoner}", style=f"bold {C_GOLD}"),
        border_style=C_GOLD,
        padding=(1, 2),
    ))
    console.print(Rule(style=C_TEAL))
    console.print()


def show_error(message: str) -> None:
    console.print(f"[bold {C_BLUE}]Error:[/bold {C_BLUE}] [{C_ERROR}]{escape(message)}[/{C_ERROR}]")


def show_progress(message: str) -> None:
    console.print(f"[{C_BLUE}]  ›  {escape(message)}[/{C_BLUE}]")


def save_export(summoner: str, data_prompt: str, system_prompt: str) -> str:
    """Write a self-contained prompt file the user can paste into any web AI.
    Returns the absolute path of the file written."""
    safe_name = summoner.replace("#", "_").replace(" ", "_")
    date_str  = datetime.date.today().isoformat()
    filename  = f"lol_analysis_{safe_name}_{date_str}.md"

    content = (
        f"# League of Legends Coaching Analysis — {summoner}\n"
        f"_Generated: {date_str}_\n\n"
        "---\n\n"
        "> **How to use this file**\n"
        "> Paste the entire content of this file into [Claude.ai](https://claude.ai),\n"
        "> [ChatGPT](https://chatgpt.com), [Gemini](https://gemini.google.com),\n"
        "> or any AI assistant, then press **Send**.\n\n"
        "---\n\n"
        f"{system_prompt}\n\n"
        "Also include in your analysis:\n"
        "- **Why this player is stuck at their current rank** — identify the specific "
        "habits or patterns holding them back.\n"
        "- **Top 3 highest-leverage improvements to climb** — concrete, rank-appropriate "
        "changes they can make in their very next session.\n\n"
        "---\n\n"
        f"{data_prompt}\n"
    )

    path = Path(filename).resolve()
    path.write_text(content, encoding="utf-8")
    return str(path)


def show_export_saved(filename: str) -> None:
    console.print()
    console.print(Rule(style=C_TEAL))
    console.print(f"[bold {C_GOLD}]  ✓  Export saved[/bold {C_GOLD}]")
    console.print(f"[{C_STAT}]  {escape(filename)}[/{C_STAT}]")
    console.print(
        f"\n[{C_BLUE}]  Paste the entire file into Claude.ai, ChatGPT, Gemini, "
        f"or any AI assistant to get your coaching report.[/{C_BLUE}]"
    )
    console.print(Rule(style=C_TEAL))
    console.print()
