def get_provider_api_base(model: str) -> str | None:
    """Get the API base URL for a model using litellm.

    This function tries multiple approaches to determine the API base URL:
    1. First tries litellm.get_api_base() which handles OpenAI, Gemini, Mistral
    2. Falls back to ProviderConfigManager.get_provider_model_info() for providers
       like Anthropic that have ModelInfo classes with get_api_base() methods

    Args:
        model: The model name (e.g., 'gpt-4', 'anthropic/claude-sonnet-4-5-20250929')

    Returns:
        The API base URL if found, None otherwise.
    """
    # First try get_api_base (handles OpenAI, Gemini with specific URL patterns)
    try:
        api_base = litellm.get_api_base(model, {})
        if api_base:
            return api_base
    except Exception:
        pass

    # Fall back to ProviderConfigManager for providers like Anthropic
    try:
        # Get the provider from the model
        _, provider_name, _, _ = get_llm_provider(model)
        if provider_name:
            # Convert provider name to LlmProviders enum
            try:
                provider_enum = LlmProviders(provider_name)
                model_info = ProviderConfigManager.get_provider_model_info(
                    model, provider_enum
                )
                if model_info and hasattr(model_info, 'get_api_base'):
                    return model_info.get_api_base()
            except ValueError:
                pass  # Provider not in enum
    except Exception:
        pass

    return None