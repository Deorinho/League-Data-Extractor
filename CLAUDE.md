# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install in editable mode with dev dependencies
pip install -e ".[dev]"

# Run the CLI (after install)
lol-stats

# Run tests
pytest tests/

# Run a single test file
pytest tests/test_riot.py -v
```

## Architecture

**Purpose**: CLI tool that fetches a League of Legends summoner's recent ranked match data via the Riot Games API and passes it to an AI model (Claude or local Ollama) to generate a coaching analysis.

**High-level flow**:
1. `cli.py` → parses args, reads config, orchestrates the pipeline
2. `fetchers/riot.py` → Riot API client: resolves Riot ID (GameName#Tag) → PUUID → match IDs → match data + timelines
3. `analyzer.py` → transforms raw match JSON into a structured prompt using `COACHING_SYSTEM_PROMPT`
4. `ai/claude.py` or `ai/ollama.py` → sends prompt to Claude API or local Ollama; selected via config `default_ai`
5. `display.py` → renders AI output to terminal using `rich`

**Package name**: The installable package is `lol-analyzer` (pyproject.toml), but the source directory is `lol_summoner_analyzer/`. Internal imports use `lol_summoner_analyzer.*`.

**Configuration** (`config.py`): Persisted at `~/.lol-config.json` (mode 0o600). Priority: env vars > disk config > defaults. Relevant keys: `RIOT_API_KEY`, `ANTHROPIC_API_KEY`, `OLLAMA_HOST`, `default_region`, `default_ai` (`claude` | `ollama`), `default_games`, `ollama_model`.

**Riot API routing** (`fetchers/riot.py`): Platform regions (e.g. `na1`, `euw1`) map to regional routing endpoints (`americas`, `europe`, `asia`, `sea`) for Account V1 and Match V5 calls. Rate-limit headers (`Retry-After`) are respected.

**AI backends**:
- `ai/claude.py` — uses `anthropic` SDK, defaults to `claude-sonnet-4-5`
- `ai/ollama.py` — hits `http://localhost:11434/api/chat`, defaults to `llama3`, 600s timeout

## Current State

`cli.py`, `analyzer.py`, and `display.py` are empty stubs — the implementation has not been written yet. `fetchers/riot.py`, `ai/claude.py`, `ai/ollama.py`, and `config.py` are implemented.
