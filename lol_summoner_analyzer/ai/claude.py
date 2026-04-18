"""
Anthropic Claude API backend.
Requires the `anthropic` package and a valid API key.
"""
import anthropic
from lol_summoner_analyzer.analyzer import COACHING_SYSTEM_PROMPT

# Default model — change to claude-opus-4-5 for deeper analysis (costs more).
DEFAULT_MODEL = "claude-sonnet-4-5"


def analyse(prompt: str, api_key: str, model: str = DEFAULT_MODEL) -> str:
    """
    Send a coaching prompt to the Claude API and return the response text.

    Args:
        prompt:  The user-facing prompt (built by analyzer.build_prompt).
        api_key: Anthropic API key.
        model:   Model identifier string.

    Returns:
        The model's coaching report as a plain string.

    Raises:
        anthropic.APIError: On API-level failures (bad key, quota, etc.).
    """
    client = anthropic.Anthropic(api_key=api_key)
    message = client.messages.create(
        model=model,
        max_tokens=2048,
        system=COACHING_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text