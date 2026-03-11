"""
claude_api.py — Anthropic Claude API wrapper.

Provides a simple helper for calling Claude with streaming support.
Used by all agents to generate responses.
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import anthropic
from config import ANTHROPIC_API_KEY, MODEL_NAME


def get_client() -> anthropic.Anthropic:
    """
    Return a configured Anthropic client.

    Raises:
        EnvironmentError: If ANTHROPIC_API_KEY is not set.
    """
    key = ANTHROPIC_API_KEY or os.environ.get("ANTHROPIC_API_KEY", "")
    if not key:
        raise EnvironmentError(
            "ANTHROPIC_API_KEY is not set. "
            "Export it with: export ANTHROPIC_API_KEY='your-key'"
        )
    return anthropic.Anthropic(api_key=key)


def call_claude(
    system_prompt: str,
    user_message: str,
    model: str = None,
    max_tokens: int = 2048,
    temperature: float = 0.7,
) -> str:
    """
    Call the Claude API and return the full text response.

    Uses streaming internally to avoid HTTP timeouts on long outputs.

    Args:
        system_prompt: The agent's system-level instructions.
        user_message:  The user's query or task.
        model:         Override the default model (uses config.MODEL_NAME).
        max_tokens:    Maximum output tokens.
        temperature:   Sampling temperature (0.0–1.0).

    Returns:
        Full response text as a string.

    Raises:
        anthropic.APIError: On API-level failures.
        EnvironmentError:   If API key is missing.
    """
    client = get_client()
    model = model or MODEL_NAME

    full_text = []
    with client.messages.stream(
        model=model,
        max_tokens=max_tokens,
        system=system_prompt,
        messages=[{"role": "user", "content": user_message}],
    ) as stream:
        for text in stream.text_stream:
            full_text.append(text)

    return "".join(full_text)


def call_claude_with_image(
    system_prompt: str,
    user_message: str,
    image_base64: str,
    media_type: str = "image/jpeg",
    model: str = None,
    max_tokens: int = 4096,
) -> str:
    """
    Call Claude with a base64-encoded image (vision/multimodal).

    Args:
        system_prompt: Agent system instructions.
        user_message:  Student's question about the image.
        image_base64:  Base64-encoded image data (no data: URI prefix).
        media_type:    MIME type — image/jpeg, image/png, image/gif, image/webp.
        model:         Model override.
        max_tokens:    Maximum output tokens.

    Returns:
        Full response text.
    """
    client = get_client()
    model = model or MODEL_NAME

    content = [
        {
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": media_type,
                "data": image_base64,
            },
        },
        {"type": "text", "text": user_message or "Please analyze this image and help me understand or solve the problem shown."},
    ]

    full_text = []
    with client.messages.stream(
        model=model,
        max_tokens=max_tokens,
        system=system_prompt,
        messages=[{"role": "user", "content": content}],
    ) as stream:
        for text in stream.text_stream:
            full_text.append(text)

    return "".join(full_text)


def call_claude_with_history(
    system_prompt: str,
    messages: list,
    model: str = None,
    max_tokens: int = 2048,
) -> str:
    """
    Call Claude with a multi-turn conversation history.

    Args:
        system_prompt: System-level instructions.
        messages:      List of {"role": "user"|"assistant", "content": str} dicts.
        model:         Model override.
        max_tokens:    Maximum output tokens.

    Returns:
        Full response text.
    """
    client = get_client()
    model = model or MODEL_NAME

    full_text = []
    with client.messages.stream(
        model=model,
        max_tokens=max_tokens,
        system=system_prompt,
        messages=messages,
    ) as stream:
        for text in stream.text_stream:
            full_text.append(text)

    return "".join(full_text)
