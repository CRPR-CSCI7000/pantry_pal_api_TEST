import os

import openai

from config import OPENAI_API_KEY


class _DummyCompletions:
    def create(self, *args, **kwargs):
        raise RuntimeError(
            "OpenAI API key is not configured. Set OPENAI_API_KEY to use OpenAI features."
        )


class _DummyChat:
    def __init__(self):
        self.completions = _DummyCompletions()


class DummyOpenAI:
    def __init__(self):
        self.chat = _DummyChat()


def get_openai_client():
    """Return either the configured OpenAI client or a dummy client when key is missing."""
    if not OPENAI_API_KEY:
        return DummyOpenAI()

    # Set API key on the openai module for backwards compatibility with older code
    openai.api_key = OPENAI_API_KEY
    return openai


openai_client = get_openai_client()


def has_openai_key():
    return bool(OPENAI_API_KEY)
