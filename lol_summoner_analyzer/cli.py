"""CLI entry point: lol-stats"""
from __future__ import annotations

from typing import Optional

import typer

from lol_summoner_analyzer import config, display
from lol_summoner_analyzer.analyzer import build_prompt
from lol_summoner_analyzer.fetchers.riot import RiotClient, RioteApiError

app = typer.Typer(add_completion=False, help="League of Legends ranked performance analyzer.")


@app.command()
def analyse(
    summoner: str = typer.Argument(..., help="Riot ID in GameName#TAG format, e.g. Faker#KR1"),
    region: Optional[str] = typer.Option(None, "--region", "-r", help="Platform region (na1, euw1, kr, …)"),
    games: int = typer.Option(0, "--games", "-n", help="Number of recent games to analyze (default 20)"),
    model: Optional[str] = typer.Option(None, "--model", "-m", help="Claude model override"),
    no_timeline: bool = typer.Option(False, "--no-timeline", help="Skip per-game timelines (faster, no early-game diffs)"),
) -> None:
    cfg = config.load()

    riot_key: str = cfg.get("riot_api_key", "")
    anthropic_key: str = cfg.get("anthropic_api_key", "")
    used_region: str = region or cfg.get("default_region", "na1")
    num_games: int = games or int(cfg.get("default_games", 20))

    if not riot_key:
        display.show_error("No Riot API key found. Set the RIOT_API_KEY environment variable.")
        raise typer.Exit(1)
    if not anthropic_key:
        display.show_error("No Anthropic API key found. Set the ANTHROPIC_API_KEY environment variable.")
        raise typer.Exit(1)
    if "#" not in summoner:
        display.show_error("Summoner must be in GameName#TAG format, e.g. Faker#KR1")
        raise typer.Exit(1)

    game_name, tag_line = summoner.split("#", 1)
    client = RiotClient(riot_key, used_region)

    try:
        display.show_progress(f"Resolving {summoner}...")
        puuid = client.get_puuid(game_name, tag_line)

        display.show_progress(f"Fetching last {num_games} ranked matches...")
        match_ids = client.get_ranked_match_ids(puuid, count=num_games)

        if not match_ids:
            display.show_error("No ranked games found for this summoner.")
            raise typer.Exit(1)

        matches: list[dict] = []
        timelines: list[dict] = []
        total = len(match_ids)
        for idx, mid in enumerate(match_ids, 1):
            display.show_progress(f"  [{idx}/{total}] {mid}")
            matches.append(client.get_match(mid))
            if not no_timeline:
                timelines.append(client.get_timeline(mid))

    except RioteApiError as exc:
        display.show_error(str(exc))
        raise typer.Exit(1)

    display.show_progress("Sending to Claude for analysis...")
    prompt = build_prompt(matches, timelines, puuid)

    from lol_summoner_analyzer.ai.claude import analyse as claude_analyse
    used_model: str = model or "claude-sonnet-4-5"
    try:
        report = claude_analyse(prompt, anthropic_key, model=used_model)
    except Exception as exc:
        display.show_error(f"Claude API error: {exc}")
        raise typer.Exit(1)

    display.show_report(summoner, report)


def main() -> None:
    app()
