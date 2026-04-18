"""Terminal rendering using Rich."""
import datetime
from pathlib import Path

from rich.console import Console
from rich.markdown import Markdown
from rich.markup import escape
from rich.panel import Panel
from rich.rule import Rule
from rich.text import Text

# ── Colour palette ───────────────────────────────────────────────────────────
# Change any hex value here to restyle the whole CLI.
C_BORDER       = "#C89B3C"   # Panel / rule border  (gold)
C_TITLE        = "#F0E6D3"   # Panel title text      (parchment white)
C_LABEL        = "#C89B3C"   # "Error:" / "Rank:" labels (gold)
C_ERROR_MSG    = "#FF4C4C"   # Error message body    (red)
C_PROGRESS     = "#785A28"   # Dim progress lines    (dark gold)
C_HEADER_RULE  = "#0BC4E3"   # Divider rule          (League blue)
# ─────────────────────────────────────────────────────────────────────────────

console = Console()


def show_report(summoner: str, report: str) -> None:
    console.print()
    console.print(Rule(style=C_HEADER_RULE))
    console.print(
        Panel(
            Markdown(report),
            title=Text(f"Coaching Report — {summoner}", style=f"bold {C_TITLE}"),
            border_style=C_BORDER,
            padding=(1, 2),
        )
    )
    console.print(Rule(style=C_HEADER_RULE))
    console.print()


def show_error(message: str) -> None:
    console.print(f"[bold {C_LABEL}]Error:[/bold {C_LABEL}] [{C_ERROR_MSG}]{escape(message)}[/{C_ERROR_MSG}]")


def show_progress(message: str) -> None:
    console.print(f"[{C_PROGRESS}]{escape(message)}[/{C_PROGRESS}]")


def save_export(summoner: str, data_prompt: str, system_prompt: str) -> str:
    """
    Write a self-contained markdown file the user can paste into any web AI.
    Returns the filename that was written.
    """
    # ── File name ─────────────────────────────────────────────────────────────
    safe_name = summoner.replace("#", "_").replace(" ", "_")
    date_str = datetime.date.today().isoformat()
    filename = f"lol_analysis_{safe_name}_{date_str}.md"

    # ── File content ──────────────────────────────────────────────────────────
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
    console.print(Rule(style=C_HEADER_RULE))
    console.print(
        f"[bold {C_LABEL}]Export saved →[/bold {C_LABEL}] "
        f"[{C_TITLE}]{filename}[/{C_TITLE}]"
    )
    console.print(
        f"[{C_PROGRESS}]Paste the entire file into Claude.ai, ChatGPT, Gemini, "
        f"or any AI assistant to get your coaching report.[/{C_PROGRESS}]"
    )
    console.print(Rule(style=C_HEADER_RULE))
    console.print()
