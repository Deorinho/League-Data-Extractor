# League Analyzer

A CLI tool that pulls your last 20 ranked games from the Riot API and generates a personalised coaching report — early game weaknesses, micro review, macro review, and why you're stuck at your rank.

By default it saves a ready-to-use file you can paste into any free AI (Claude.ai, ChatGPT, Gemini). If you have an Anthropic API key you can get the report directly in your terminal with `--ai`.

---

## How it works

```text
lol-stats Doublelift#NA1
  → fetches last 20 ranked games from Riot API
  → calculates CS/min, KDA, gold diff @10, vision score, win rate …
  → saves lol_analysis_Doublelift_NA1_2026-04-18.md
  → paste that file into any AI → get your coaching report
```

With `--ai`:

```text
╭─────────────────── Coaching Report — Doublelift#NA1 ───────────────────╮
│                                                                          │
│ ## Early Game Weaknesses                                                 │
│ - Average CS diff at 10 minutes: -8 across all games ...                │
│                                                                          │
│ ## Micro Review                                                          │
│ - KDA of 2.1 suggests dying too often in losing trades ...              │
│                                                                          │
│ ## Macro Review                                                          │
│ - Vision score averaging 18 is below the rank average ...               │
╰──────────────────────────────────────────────────────────────────────────╯
```

---

## Prerequisites

**Required for everyone:**

1. **Python 3.10 or newer** — [download here](https://www.python.org/downloads/). During install on Windows, check **"Add Python to PATH"**.
2. **A Riot API key** — free, takes 2 minutes (see Step 1 below).

**Optional — only needed if you want the report printed directly in your terminal:**

1. **An Anthropic API key** — requires a paid account with a small credit balance (see Step 2 below).

---

## Step 1 — Get your Riot API key

1. Go to [https://developer.riotgames.com](https://developer.riotgames.com) and sign in with your League account.
2. Your **Development API Key** is shown on the dashboard. Copy it.
3. It expires every 24 hours — regenerate it on the same page when it stops working.

> If you plan to use this daily, apply for a **Personal API Key** on the same site. It doesn't expire.

---

## Step 2 — Get your Anthropic API key (optional)

Only needed if you want to use `--ai` for an instant in-terminal report.

1. Go to [https://console.anthropic.com](https://console.anthropic.com) and create an account.
2. Add a small amount of credit (a few dollars covers hundreds of analyses).
3. Go to **API Keys** → **Create Key**. Copy it.

---

## Step 3 — Install the tool

Open a terminal (Command Prompt or PowerShell on Windows, Terminal on Mac/Linux) and run:

```bash
git clone https://github.com/Deorinho/League-Data-Extractor.git
cd League-Data-Extractor
pip install .
```

The `lol-stats` command is now available in your terminal.

---

## Step 4 — Set your API key(s)

Set them once per terminal session:

**Windows (Command Prompt):**

```cmd
set RIOT_API_KEY=RGAPI-your-key-here
set ANTHROPIC_API_KEY=sk-ant-your-key-here
```

**Windows (PowerShell):**

```powershell
$env:RIOT_API_KEY="RGAPI-your-key-here"
$env:ANTHROPIC_API_KEY="sk-ant-your-key-here"
```

**Mac / Linux:**

```bash
export RIOT_API_KEY=RGAPI-your-key-here
export ANTHROPIC_API_KEY=sk-ant-your-key-here
```

> To avoid setting these every time, add the `export` lines to your `~/.bashrc` or `~/.zshrc` on Mac/Linux, or set them as permanent System Environment Variables on Windows.
>
> `ANTHROPIC_API_KEY` is only required if you use `--ai`.

---

## Step 5 — Run it

**Default — saves a file you paste into any AI (no Anthropic key needed):**

```bash
lol-stats YourName#TAG
```

This creates `lol_analysis_YourName_TAG_<date>.md` in your current folder. Open it, copy everything, paste it into [Claude.ai](https://claude.ai), [ChatGPT](https://chatgpt.com), or [Gemini](https://gemini.google.com), and send.

**With `--ai` — prints the report directly in your terminal:**

```bash
lol-stats YourName#TAG --ai
```

Requires `ANTHROPIC_API_KEY` to be set.

---

## Examples

```bash
# Save export file (default) — no Anthropic key needed
lol-stats Doublelift#NA1

# Get report directly in terminal (requires Anthropic key)
lol-stats Doublelift#NA1 --ai

# EUW / Korean player — specify region
lol-stats Faker#KR1 --region kr

# Analyze only the last 10 games
lol-stats Doublelift#NA1 --games 10

# Skip early-game timeline data (about 2x faster, no gold/CS diffs)
lol-stats Doublelift#NA1 --no-timeline

# Use a different Claude model with --ai
lol-stats Doublelift#NA1 --ai --model claude-opus-4-7
```

---

## All options

```text
lol-stats [NAME#TAG] [OPTIONS]

Arguments:
  NAME#TAG         Your Riot ID (required), e.g. Doublelift#NA1

Options:
  -r, --region     Platform region: na1, euw1, kr, br1, la1, la2, eun1, jp1 (default: na1)
  -n, --games      Number of recent ranked games to analyze (default: 20)
      --ai         Send metrics to Claude API and print report in terminal
  -m, --model      Claude model override — only used with --ai (default: claude-sonnet-4-6)
      --no-timeline  Skip per-game timeline fetching — faster but no gold/CS diffs @10 min
```

---

## Supported Regions

| Region               | Code   |
| -------------------- | ------ |
| North America        | `na1`  |
| Europe West          | `euw1` |
| Europe Nordic & East | `eun1` |
| Korea                | `kr`   |
| Japan                | `jp1`  |
| Brazil               | `br1`  |
| Latin America North  | `la1`  |
| Latin America South  | `la2`  |
| Oceania              | `oc1`  |

---

## Troubleshooting

**`lol-stats: command not found`**
> Python's scripts folder is not in your PATH. Try `python -m lol_summoner_analyzer.cli YourName#TAG` instead, or reinstall Python and check "Add to PATH".

**`Riot API 403` or `Riot API 401`**
> Your Riot key is invalid or expired. Regenerate it at [developer.riotgames.com](https://developer.riotgames.com).

**`No ranked games found`**
> The account has no ranked Solo/Duo games this split, or the Riot ID is wrong. Double-check the exact name and tag shown in the client.

**`Claude API error` (when using --ai)**
> Your Anthropic key is wrong or your account has no credit. Check [console.anthropic.com](https://console.anthropic.com).
