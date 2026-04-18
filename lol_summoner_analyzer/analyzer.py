"""
Transforms raw Riot match data into a structured AI coaching prompt.
"""
from __future__ import annotations

from lol_summoner_analyzer.fetchers.riot import mirror_participant_id

COACHING_SYSTEM_PROMPT = """\
You are an expert League of Legends coach. Analyze the player's recent ranked match data and provide \
specific, actionable feedback structured in exactly three sections:

## Early Game Weaknesses
Focus on CS differentials at 10 minutes, first-blood involvement, early deaths, and lane priority.

## Micro Review
Individual mechanics: CS accuracy, trading patterns, death causes, cooldown usage, positioning in fights.

## Macro Review
Map awareness, objective control, roaming, vision score trends, teamfight decision-making.

Rules:
- Reference actual numbers from the data.
- Be concise — 3-5 bullet points per section.
- Prioritize the highest-impact improvements, not generic advice.
- If the sample is too small to draw a conclusion, say so.\
"""


def build_prompt(matches: list[dict], timelines: list[dict], puuid: str) -> str:
    """Build the user-facing coaching prompt from raw match and timeline data."""
    rows: list[str] = []
    agg = {
        "wins": 0, "kills": 0, "deaths": 0, "assists": 0,
        "cs": 0, "duration_s": 0, "vision": 0, "gold": 0, "damage": 0,
        "games": 0,
        "early_gold_diffs": [],
        "early_cs_diffs": [],
    }

    for i, match in enumerate(matches):
        participant = _find_player(match, puuid)
        if participant is None:
            continue

        duration_s = match["info"]["gameDuration"]
        duration_m = max(duration_s / 60, 1)
        win = participant["win"]
        k = participant["kills"]
        d = participant["deaths"]
        a = participant["assists"]
        cs = participant.get("totalMinionsKilled", 0) + participant.get("neutralMinionsKilled", 0)
        cs_pm = round(cs / duration_m, 1)
        vision = participant.get("visionScore", 0)
        gold = participant["goldEarned"]
        damage = participant.get("totalDamageDealtToChampions", 0)
        champ = participant["championName"]
        role = participant.get("teamPosition") or participant.get("individualPosition", "?")
        kda = round(_safe_div(k + a, max(d, 1)), 2)

        gold_diff_10 = cs_diff_10 = 0
        if i < len(timelines):
            gold_diff_10, cs_diff_10 = _early_diffs(timelines[i], participant["participantId"])
            agg["early_gold_diffs"].append(gold_diff_10)
            agg["early_cs_diffs"].append(cs_diff_10)

        result = "WIN" if win else "LOSS"
        rows.append(
            f"  {result} | {champ:<15} | {role:<8} | {k}/{d}/{a} (KDA {kda}) | "
            f"CS {cs} ({cs_pm}/m) | Vision {vision} | Gold {gold} | Dmg {damage} | "
            f"GoldDiff@10 {gold_diff_10:+d} | CSDiff@10 {cs_diff_10:+d}"
        )

        agg["wins"] += int(win)
        agg["kills"] += k
        agg["deaths"] += d
        agg["assists"] += a
        agg["cs"] += cs
        agg["duration_s"] += duration_s
        agg["vision"] += vision
        agg["gold"] += gold
        agg["damage"] += damage
        agg["games"] += 1

    n = agg["games"] or 1
    avg_dur_m = max(agg["duration_s"] / n / 60, 1)
    win_rate = round(agg["wins"] / n * 100)
    avg_kda = round(_safe_div(agg["kills"] + agg["assists"], max(agg["deaths"], 1)), 2)
    avg_cs_pm = round(agg["cs"] / n / avg_dur_m, 1)
    avg_vision = round(agg["vision"] / n, 1)
    avg_gold = round(agg["gold"] / n)
    avg_dmg = round(agg["damage"] / n)

    def _fmt_avg(lst: list) -> str:
        return f"{round(sum(lst) / len(lst)):+d}" if lst else "N/A"

    summary = (
        f"=== LAST {n} RANKED SOLO/DUO GAMES ===\n"
        f"Win Rate : {win_rate}%  ({agg['wins']}W / {n - agg['wins']}L)\n"
        f"Avg KDA  : {avg_kda}   Avg CS/min : {avg_cs_pm}   Avg Vision : {avg_vision}\n"
        f"Avg Gold : {avg_gold}   Avg Damage : {avg_dmg}\n"
        f"Avg Gold Diff @10 : {_fmt_avg(agg['early_gold_diffs'])}   "
        f"Avg CS Diff @10 : {_fmt_avg(agg['early_cs_diffs'])}\n\n"
        "=== PER-GAME BREAKDOWN ===\n"
        + "\n".join(rows)
    )

    return (
        f"Please analyze this player's last {n} ranked games and provide coaching feedback.\n\n"
        + summary
    )


def _safe_div(a: float, b: float) -> float:
    return a / b if b else 0.0


def _find_player(match: dict, puuid: str) -> dict | None:
    for p in match["info"]["participants"]:
        if p["puuid"] == puuid:
            return p
    return None


def _early_diffs(timeline: dict, participant_id: int) -> tuple[int, int]:
    """Extract gold and CS differential vs lane opponent at 10 minutes."""
    opponent_id = mirror_participant_id(participant_id)
    frames = timeline.get("info", {}).get("frames", [])

    target_frame = min(10, len(frames) - 1)
    if target_frame < 1:
        return 0, 0

    pf = frames[target_frame].get("participantFrames", {})

    # Riot returns participantFrames keyed as strings or ints depending on version
    def _pf(pid: int) -> dict:
        return pf.get(str(pid), pf.get(pid, {}))

    mine = _pf(participant_id)
    opp = _pf(opponent_id)

    gold_diff = mine.get("totalGold", 0) - opp.get("totalGold", 0)
    cs_diff = (
        mine.get("minionsKilled", 0) + mine.get("jungleMinionsKilled", 0)
        - opp.get("minionsKilled", 0) - opp.get("jungleMinionsKilled", 0)
    )
    return gold_diff, cs_diff
