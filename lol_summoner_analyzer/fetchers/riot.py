"""
Riot Games API Client (Match V5 + Account V1).

Handles:
    - Riot ID -> PUUID Resolution
    - Ranked solo/duo match ID listing
    - Full match detail 
    - per-minute match timeline (gold, CS, XP diffs)
    - Rate=limit retry with Retry-After header respect


API DOCS:  https://developer.riotgames.com/apis
"""

import time
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


class RioteApiError(Exception):
    """
    Raised when the Riot API returns a non-2xx response.
    """
    def __init__(self, status_code:int, message:str) -> None:
        self.status_code = status_code
        super().__init__(f"Riot API {status_code}: {message}")


class RiotClient:
    """
    Thin wrapper around the Riot REST API.
    """
    def __init__(self, api_key:str, region:str = "na1") -> None:
        self.region
        self.routing = PLATFORM_TO_REGION.get(self.region, "americas")
        self._session: Session = requests.Session()
        self._session.headers.update({
            "X-Riot-Token": api_key,
            "Accept": "application/json",
        })

# private helpers


def get(self, url: str, params: dict | None = None, retries: int = 3) -> dict:
    """
    GET a Riot API endpoint.
    Retries up to 'retries' times on 429 (rate limit), respecting the Retry-After header when present.
    """
    for attempt in range(retries):
        try:
            response = self._session.get(url, params=params or {}, timeout = 10)
        except requests.exceptions.Timeout:
            if attempt == retries -1:
                raise RioteApiError(0, f"Request timed out after 10s")
            time.sleep(2**attempt)
            continue
        except requests.exceptions.ConnectionError as exc:
            raise RioteApiError(0, f"Network Error: {exc}")

        if response.status_code == 429:
            wait = int(response.headers.get("Retry-After", 5))
            time.sleep(wait)
            continue
        if not response.ok:
            try:
                msg = response.json().get("status", {}).get("message", response.text)
            except ValueError:
                msg = response.text
                raise RioteApiError(response.status_code, msg)
            
    return RioteApiError(429, "Rate limit: exhausted all retry attempts...")


# Public API

def get_puuid(self, game_name: str, tag_line: str) -> str:
    """
    Resolve a Riote ID (GameName + tagLine) to a PUUID.
    """
    url = (
            f"https://{self.routing}.api.riotgames.com"
            f"/riot/account/v1/accounts/by-riot-id/{game_name}/{tag_line}"
        )
    return self._get(url)["puuid"]

def get_ranked_match_ids(self, puuid: str, count: int = 20) -> list[str]:
    """
    Return the most recent ranked solo/duo match IDs for a given PUUID.
    """
    url = (
            f"https://{self.routing}.api.riotgames.com"
            f"/lol/match/v5/matches/by-puuid/{puuid}/ids"
        )
    return self._get(url, {
        "queue": RANKED_SOLO_DUO,
        "type": "ranked",
        "count": min(count,100), #Riot caps at 100.
    })

def get_match(self, match_id:str) -> dict:
    """
    Return full match data for a given match ID.
    """
    url = (
            f"https://{self.routing}.api.riotgames.com"
            f"/lol/match/v5/matches/{match_id}"
        )
    return self._get(url)


def get_timeline(self, match_id:str) -> dict:
    """
    Returns the per-minute timeline for a match.
    Used to derive early-game gold, CS, XP differentials.
    """
    url = (
            f"https://{self.routing}.api.riotgames.com"
            f"/lol/match/v5/matches/{match_id}/timeline"
        )
    return self._get(url)

# for convenience sake

def find_player(match: dict, puuid: str) -> dict | None:
    """
    Return the participant dict for the given PUUID, or None.
    """
    for participant in match["info"]["participants"]:
        if participant["puuid"] == puuid:
            return participant
    return None


def mirror_participant_id(participant_id: int) -> int:
    """
    Return the approximate lane opponent's participantId.
    Team 1 = IDs 1-5, Team 2 = IDs 6-10.
    This is a best-effort heuristic — positional matching in the
    timeline is not always reliable.
    """
    return participant_id + 5 if participant_id <=5 else participant_id - 5