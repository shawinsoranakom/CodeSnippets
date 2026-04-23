def fetch_live_watsonx_models(user_id: UUID | str | None, model_type: str = "llm") -> list[dict]:
    """Fetch live WatsonX models from the configured WatsonX instance.

    Args:
        user_id: The user ID to look up the WatsonX URL
        model_type: "llm" or "embeddings"

    Returns:
        List of model metadata dicts, or empty list if unable to fetch
    """
    # Get the configured WatsonX URL
    watsonx_url = get_provider_variable_value(user_id, "WATSONX_URL")
    if not watsonx_url:
        # Try first default URL if none configured
        watsonx_url = IBM_WATSONX_URLS[0] if IBM_WATSONX_URLS else None
        if not watsonx_url:
            return []

    try:
        if model_type == "llm":
            model_names = get_watsonx_llm_models(watsonx_url)
        else:
            model_names = get_watsonx_embedding_models(watsonx_url)

        # Convert to model metadata format
        return [
            create_model_metadata(
                provider="IBM WatsonX",
                name=name,
                icon="IBM",
                model_type=model_type if model_type == "llm" else "embeddings",
                tool_calling=model_type == "llm",
                default=i < MIN_DEFAULT_MODELS,  # Mark first 5 as default
            )
            for i, name in enumerate(model_names)
        ]
    except Exception:  # noqa: BLE001
        logger.debug(f"Could not fetch live WatsonX {model_type} models from {watsonx_url}")
        return []