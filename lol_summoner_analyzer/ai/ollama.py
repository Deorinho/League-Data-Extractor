"""
Ollama local model backend.

Communicates with a running Ollama instance via its REST API.
Install Ollama: https://ollama.com
Pull a model:  ollama pull llama3

The /api/chat endpoint is used (not /api/generate) so that the
system prompt is handled correctly by all model families.
"""
import requests
from lol_summoner_analyzer.analyzer import COACHING_SYSTEM_PROMPT

DEFAULT_HOST  = "http://localhost:11434"
DEFAULT_MODEL = "llama3"

# Generous timeout — large models can take a while on CPU.
REQUEST_TIMEOUT = 600


class OllamaError(Exception):
    """Raised when Ollama is unreachable or returns an unexpected response."""


def list_models(host: str = DEFAULT_HOST) -> list[str]:
    """
    Return the names of all locally available Ollama models.

    Raises:
        OllamaError: If Ollama is not running or the host is unreachable.
    """
    try:
        response = requests.get(f"{host}/api/tags", timeout=5)
        response.raise_for_status()
        return [m["name"] for m in response.json().get("models", [])]
    except requests.exceptions.ConnectionError:
        raise OllamaError(
            f"Cannot reach Ollama at {host}. "
            "Make sure it is running — see https://ollama.com"
        )
    except requests.exceptions.HTTPError as exc:
        raise OllamaError(f"Ollama returned an error: {exc}")


def analyse(
    prompt: str,
    model:  str = DEFAULT_MODEL,
    host:   str = DEFAULT_HOST,
) -> str:
    """
    Send a coaching prompt to a local Ollama model and return the response.

    Args:
        prompt: The user-facing prompt (built by analyzer.build_prompt).
        model:  Ollama model name (e.g. "llama3", "mistral", "gemma3").
        host:   Ollama host URL.

    Returns:
        The model's coaching report as a plain string.

    Raises:
        OllamaError: If the request fails or the response is malformed.
    """
    payload = {
        "model":  model,
        "stream": False,
        "messages": [
            {"role": "system", "content": COACHING_SYSTEM_PROMPT},
            {"role": "user",   "content": prompt},
        ],
        "options": {
            # Keep the output deterministic enough to be useful.
            "temperature": 0.3,
            "num_predict": 2048,
        },
    }
    try:
        response = requests.post(
            f"{host}/api/chat",
            json=payload,
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        return response.json()["message"]["content"]
    except requests.exceptions.ConnectionError:
        raise OllamaError(
            f"Cannot reach Ollama at {host}. "
            "Make sure it is running — see https://ollama.com"
        )
    except requests.exceptions.HTTPError as exc:
        raise OllamaError(f"Ollama returned an error: {exc}")
    except (KeyError, ValueError) as exc:
        raise OllamaError(f"Unexpected response from Ollama: {exc}")