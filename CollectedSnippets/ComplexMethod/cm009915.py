def _attempt_infer_model_provider(model_name: str) -> str | None:
    """Attempt to infer model provider from model name.

    Args:
        model_name: The name of the model to infer provider for.

    Returns:
        The inferred provider name, or `None` if no provider could be inferred.
    """
    model_lower = model_name.lower()

    # OpenAI models (including newer models and aliases)
    if any(
        model_lower.startswith(pre)
        for pre in (
            "gpt-",
            "o1",
            "o3",
            "chatgpt",
            "text-davinci",
        )
    ):
        return "openai"

    # Anthropic models
    if model_lower.startswith("claude"):
        return "anthropic"

    # Cohere models
    if model_lower.startswith("command"):
        return "cohere"

    # Fireworks models
    if model_name.startswith("accounts/fireworks"):
        return "fireworks"

    # Google models
    if model_lower.startswith("gemini"):
        return "google_vertexai"

    # AWS Bedrock models
    if model_name.startswith("amazon.") or model_lower.startswith(
        (
            "anthropic.",
            "meta.",
        )
    ):
        return "bedrock"

    # Mistral models
    if model_lower.startswith(("mistral", "mixtral")):
        return "mistralai"

    # DeepSeek models
    if model_lower.startswith("deepseek"):
        return "deepseek"

    # xAI models
    if model_lower.startswith("grok"):
        return "xai"

    # Perplexity models
    if model_lower.startswith("sonar"):
        return "perplexity"

    # Upstage models
    if model_lower.startswith("solar"):
        return "upstage"

    return None