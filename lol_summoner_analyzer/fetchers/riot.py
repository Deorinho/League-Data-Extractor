"""
Riot Games API Client (Match V5 + Account V1).

Handles:
    - Riot ID -> PUUID Resolution
    - Ranked solo/duo match ID listing
    - Full match detail
    - Per-minute match timeline (gold, CS diffs)
    - Rate-limit retry with Retry-After header respect

API DOCS:  https://developer.riotgames.com/apis
"""

import time
from dataclasses import dataclass
from typing import Any

import requests
from requests import Session


# Queue ID for Ranked Solo/Duo
RANKED_SOLO_DUO = 420

# Maps platform routing values to regional routing values.
# Regional routing is required for Account V1 and Match V5.
PLATFORM_TO_REGION: dict[str, str] = {
    "na1":  "americas",
    "na":   "americas",
    "br1":  "americas",
    "la1":  "americas",
    "la2":  "americas",
    "euw1": "europe",
    "eun1": "europe",
    "tr1":  "europe",
    "ru":   "europe",
    "kr":   "asia",
    "jp1":  "asia",
    "oc1":  "sea",
    "ph2":  "sea",
    "sg2":  "sea",
    "th2":  "sea",
    "tw2":  "sea",
    "vn2":  "sea",
}


class RiotApiError(Exception):
    """Raised when the Riot API returns a non-2xx response."""

    def __init__(self, status_code: int, message: str) -> None:
        self.status_code = status_code
        super().__init__(f"Riot API {status_code}: {message}")


@dataclass(frozen=True)
class RankInfo:
    """Immutable snapshot of a player's current ranked position."""

    tier: str      # e.g. "Gold"
    division: str  # e.g. "II"
    lp: int
    wins: int
    losses: int

    @classmethod
    def from_api(cls, entry: dict[str, Any]) -> "RankInfo":
        return cls(
            tier=entry["tier"].capitalize(),
            division=entry["rank"],
            lp=entry["leaguePoints"],
            wins=entry["wins"],
            losses=entry["losses"],
        )

    def __str__(self) -> str:
        return f"{self.tier} {self.division} ({self.lp} LP)"


class RiotClient:
    """Thin wrapper around the Riot REST API.

    Supports use as a context manager to ensure the underlying HTTP session
    is closed when done:

        with RiotClient(api_key, region) as client:
            puuid = client.get_puuid(name, tag)
    """

    def __init__(self, api_key: str, region: str = "na1") -> None:
        self.region = region
        self.routing = PLATFORM_TO_REGION.get(region, "americas")
        self._session: Session = requests.Session()
        self._session.headers.update({
            "X-Riot-Token": api_key,
            "Accept": "application/json",
        })

    def __enter__(self) -> "RiotClient":
        return self

    def __exit__(self, *_: Any) -> None:
        self._session.close()

    # --- URL helpers ---

    def _platform_url(self, path: str) -> str:
        """Build a platform-scoped URL (Summoner V4, League V4)."""
        return f"https://{self.region}.api.riotgames.com{path}"

    def _regional_url(self, path: str) -> str:
        """Build a regional-scoped URL (Account V1, Match V5)."""
        return f"https://{self.routing}.api.riotgames.com{path}"

    # --- HTTP layer ---

    def _get(self, url: str, params: dict[str, Any] | None = None, retries: int = 3) -> Any:
        """
        GET a Riot API endpoint, retrying on 429 with Retry-After back-off.
        Returns the parsed JSON body (dict or list depending on the endpoint).
        """
        for attempt in range(retries):
            try:
                response = self._session.get(url, params=params or {}, timeout=10)
            except requests.exceptions.Timeout:
                if attempt == retries - 1:
                    raise RiotApiError(0, "Request timed out after 10s")
                time.sleep(2 ** attempt)
                continue
            except requests.exceptions.ConnectionError as exc:
                raise RiotApiError(0, f"Network error: {exc}")

            if response.status_code == 429:
                wait = int(response.headers.get("Retry-After", 5))
                time.sleep(wait)
                continue

            if not response.ok:
                try:
                    msg = response.json().get("status", {}).get("message", response.text)
                except ValueError:
                    msg = response.text
                raise RiotApiError(response.status_code, msg)

            return response.json()

        raise RiotApiError(429, "Rate limit: exhausted all retry attempts")

    # --- Public API ---

    def get_puuid(self, game_name: str, tag_line: str) -> str:
        """Resolve a Riot ID (GameName + tagLine) to a PUUID."""
        url = self._regional_url(f"/riot/account/v1/accounts/by-riot-id/{game_name}/{tag_line}")
        return self._get(url)["puuid"]

    def get_ranked_match_ids(self, puuid: str, count: int = 20) -> list[str]:
        """Return the most recent ranked solo/duo match IDs for a given PUUID."""
        url = self._regional_url(f"/lol/match/v5/matches/by-puuid/{puuid}/ids")
        return self._get(url, {
            "queue": RANKED_SOLO_DUO,
            "type": "ranked",
            "count": min(count, 100),
        })

    def get_match(self, match_id: str) -> dict[str, Any]:
        """Return full match data for a given match ID."""
        return self._get(self._regional_url(f"/lol/match/v5/matches/{match_id}"))

    def get_timeline(self, match_id: str) -> dict[str, Any]:
        """Return the per-minute timeline for a match (gold, CS diffs)."""
        return self._get(self._regional_url(f"/lol/match/v5/matches/{match_id}/timeline"))

    def get_rank(self, puuid: str) -> RankInfo | None:
        """Return the RANKED_SOLO_5x5 entry for a summoner by PUUID, or None if unranked."""
        entries = self._get(self._platform_url(f"/lol/league/v4/entries/by-puuid/{puuid}"))
        for entry in entries:
            if entry.get("queueType") == "RANKED_SOLO_5x5":
                return RankInfo.from_api(entry)
        return None


def find_player(match: dict[str, Any], puuid: str) -> dict[str, Any] | None:
    """Return the participant dict for the given PUUID, or None."""
    for participant in match["info"]["participants"]:
        if participant["puuid"] == puuid:
            return participant
    return None


def mirror_participant_id(participant_id: int) -> int:
    """
    Return the approximate lane opponent's participantId.
    Team 1 = IDs 1-5, Team 2 = IDs 6-10.
    Best-effort heuristic — positional matching in the timeline is not always reliable.
    """
    return participant_id + 5 if participant_id <= 5 else participant_id - 5
