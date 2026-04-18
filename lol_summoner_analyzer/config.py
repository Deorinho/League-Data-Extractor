"""
Persistent configuration stored at ~/lol-config.json.

Priority order for sensitive keys (highest -> lowest):
    1. environment variable (RIOT_API_KEY, ANTHROPIC_API_KEY, OLLAMA_HOST)
    2. config.json on disk
    3. built-in default
"""

import json
import os
from pathlib import Path

CONFIG_DIR = Path.home()
CONFIG_FILE = CONFIG_DIR / "lol-config.json"

# All supported keys and their defaults.
DEFAULTS: dict[str, str | int] = {
    "riot_api_key": "",
    "anthropic_api_key": "",
    "default_region": "na1",
    "default_ai": "claude",
    "default_games": 20,
    "ollama_host": "http://localhost:11434",
    "ollama_model": "llama3",
}

# Maps config keys to the environment variables that override them.
ENV_OVERRIDES: dict[str, str] = {
    "riot_api_key":      "RIOT_API_KEY",
    "anthropic_api_key": "ANTHROPIC_API_KEY",
    "ollama_host":       "OLLAMA_HOST",
}


def load() -> dict[str, str | int]:
    """Returns merged config: defaults <- disk <- env vars."""
    merged: dict[str, str | int] = dict(DEFAULTS)
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE) as f:
                merged.update(json.load(f))
        except (json.JSONDecodeError, OSError):
            pass  # corrupt file — fall back to defaults silently
    for key, env in ENV_OVERRIDES.items():
        val = os.environ.get(env, "")
        if val:
            merged[key] = val
    return merged


def save(data: dict[str, str | int]) -> None:
    """Persist config to disk."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        json.dump(data, f, indent=2)
    CONFIG_FILE.chmod(0o600)


def get(key: str) -> str | int:
    """Return a single config value (with env override applied)."""
    return load().get(key, DEFAULTS.get(key, ""))
