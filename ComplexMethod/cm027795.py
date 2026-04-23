def get_model_for_provider(provider: str, model_name: str):
    """
    Creates and returns the appropriate model instance based on the provider.

    Args:
        provider: The model provider (e.g., 'openai', 'google', 'anthropic', 'groq')
        model_name: The specific model name/ID

    Returns:
        An instance of the appropriate model class

    Raises:
        ValueError: If the provider is not supported
    """
    if provider == "openai":
        return OpenAIChat(id=model_name)
    elif provider == "google":
        return Gemini(id=model_name)
    elif provider == "anthropic":
        if model_name == "claude-3-5-sonnet":
            return Claude(id="claude-3-5-sonnet-20241022", max_tokens=8192)
        elif model_name == "claude-3-7-sonnet":
            return Claude(
                id="claude-3-7-sonnet-20250219",
                max_tokens=8192,
            )
        elif model_name == "claude-3-7-sonnet-thinking":
            return Claude(
                id="claude-3-7-sonnet-20250219",
                max_tokens=8192,
                thinking={"type": "enabled", "budget_tokens": 4096},
            )
        else:
            return Claude(id=model_name)
    elif provider == "groq":
        return Groq(id=model_name)
    else:
        raise ValueError(f"Unsupported model provider: {provider}")