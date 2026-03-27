"""OpenAI client — returns configured client or dummy when key is absent."""
from django.conf import settings


class _DummyCompletions:
    def create(self, *args, **kwargs):
        raise RuntimeError(
            'OpenAI API key is not configured. Set OPENAI_API_KEY to use OpenAI features.'
        )


class _DummyChat:
    def __init__(self):
        self.completions = _DummyCompletions()


class DummyOpenAI:
    def __init__(self):
        self.chat = _DummyChat()


def has_openai_key() -> bool:
    return bool(getattr(settings, 'OPENAI_API_KEY', ''))


def get_openai_client():
    """Return a configured OpenAI client, or a dummy if the key is missing."""
    if not has_openai_key():
        return DummyOpenAI()

    from openai import OpenAI
    return OpenAI(api_key=settings.OPENAI_API_KEY)
