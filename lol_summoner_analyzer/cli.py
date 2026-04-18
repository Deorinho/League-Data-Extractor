"""CLI entry point: lol-stats"""
from __future__ import annotations

import typer

from lol_summoner_analyzer import config, display
from lol_summoner_analyzer.ai.claude import analyse as claude_analyse
from lol_summoner_analyzer.analyzer import COACHING_SYSTEM_PROMPT, build_prompt
from lol_summoner_analyzer.fetchers.riot import RiotApiError, RiotClient

app = typer.Typer(add_completion=False, help="League of Legends ranked performance analyzer.")


@app.command()
def analyse(
    summoner: str = typer.Argument(..., help="Riot ID in GameName#TAG format, e.g. Faker#KR1"),
    region: str | None = typer.Option(None, "--region", "-r", help="Platform region (na1, euw1, kr, …)"),
    games: int = typer.Option(0, "--games", "-n", help="Number of recent games to analyze (default 20)"),
    model: str | None = typer.Option(None, "--model", "-m", help="Claude model override (only used with --ai)"),
    no_timeline: bool = typer.Option(False, "--no-timeline", help="Skip per-game timelines (faster, no early-game diffs)"),
    use_ai: bool = typer.Option(False, "--ai", help="Send metrics to Claude API instead of saving a file"),
) -> None:
    cfg = config.load()

    riot_key: str = cfg.get("riot_api_key", "")
    anthropic_key: str = cfg.get("anthropic_api_key", "")
    used_region: str = region or cfg.get("default_region", "na1")
    num_games: int = games or int(cfg.get("default_games", 20))

    if not riot_key:
        display.show_error("No Riot API key found. Set the RIOT_API_KEY environment variable.")
        raise typer.Exit(1)
    if use_ai and not anthropic_key:
        display.show_error(
            "No Anthropic API key found. Set the ANTHROPIC_API_KEY environment variable "
            "or remove --ai to save metrics to a file instead."
        )
        raise typer.Exit(1)
    if "#" not in summoner:
        display.show_error("Summoner must be in GameName#TAG format, e.g. Faker#KR1")
        raise typer.Exit(1)

    game_name, tag_line = summoner.split("#", 1)
    display.show_banner()

    puuid: str = ""
    rank_info = None
    matches: list[dict] = []
    timelines: list[dict] = []

    with RiotClient(riot_key, used_region) as client:
        try:
            display.show_progress(f"Resolving {summoner}...")
            puuid = client.get_puuid(game_name, tag_line)

            rank_info = client.get_rank(puuid)
            display.show_rank_panel(rank_info)

            display.show_progress(f"Fetching last {num_games} ranked matches...")
            match_ids = client.get_ranked_match_ids(puuid, count=num_games)

            if not match_ids:
                display.show_error("No ranked games found for this summoner.")
                raise typer.Exit(1)

            with display.make_fetch_progress() as progress:
                task = progress.add_task("Fetching matches", total=len(match_ids))
                for mid in match_ids:
                    matches.append(client.get_match(mid))
                    if not no_timeline:
                        timelines.append(client.get_timeline(mid))
                    progress.advance(task)

        except RiotApiError as exc:
            display.show_error(str(exc))
            raise typer.Exit(1)
        except (KeyError, ValueError, TypeError) as exc:
            display.show_error(f"Unexpected response from Riot API: {exc}")
            raise typer.Exit(1)

    prompt = build_prompt(matches, timelines, puuid, rank_info=rank_info)

    if use_ai:
        display.show_progress("Sending to Claude for analysis...")
        used_model: str = model or "claude-sonnet-4-6"
        try:
            report = claude_analyse(prompt, anthropic_key, model=used_model)
        except Exception as exc:
            display.show_error(f"Claude API error: {exc}")
            raise typer.Exit(1)
        display.show_report(summoner, report)
    else:
        try:
            filename = display.save_export(summoner, prompt, COACHING_SYSTEM_PROMPT)
        except PermissionError:
            display.show_error("Could not write export file — no write permission in the current directory.")
            raise typer.Exit(1)
        display.show_export_saved(filename)


def main() -> None:
    app()
