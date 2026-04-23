def get_embedding_model_options(
    user_id: UUID | str | None = None,
) -> list[dict[str, Any]]:
    """Return available embedding model providers with their configuration."""
    # Get all embedding models (excluding deprecated and unsupported by default)
    all_models = get_unified_models_detailed(
        model_type="embeddings",
        include_deprecated=False,
        include_unsupported=False,
    )

    # Get disabled and explicitly enabled models for this user if user_id is provided
    disabled_models: set[str] = set()
    explicitly_enabled_models: set[str] = set()
    if user_id:
        with contextlib.suppress(Exception):
            disabled_models, explicitly_enabled_models = run_until_complete(_get_model_status(user_id))

    # Get enabled providers (those with credentials configured and validated)
    enabled_providers = set()
    if user_id:
        with contextlib.suppress(Exception):
            enabled_providers = run_until_complete(_fetch_enabled_providers_for_user(user_id))

    # Replace static defaults with actual available models from configured instances
    if enabled_providers:
        replace_with_live_models(
            all_models,
            user_id,
            enabled_providers,
            "embeddings",
            model_provider_metadata,
        )

    options = []

    # Provider-specific param mappings
    param_mappings = {
        "OpenAI": {
            "model": "model",
            "api_key": "api_key",
            "api_base": "base_url",
            "dimensions": "dimensions",
            "chunk_size": "chunk_size",
            "request_timeout": "timeout",
            "max_retries": "max_retries",
            "show_progress_bar": "show_progress_bar",
            "model_kwargs": "model_kwargs",
        },
        "Google Generative AI": {
            "model": "model",
            "api_key": "google_api_key",
            "request_timeout": "request_options",
            "model_kwargs": "client_options",
        },
        "Ollama": {
            "model": "model",
            "base_url": "base_url",
            "num_ctx": "num_ctx",
            "request_timeout": "request_timeout",
            "model_kwargs": "model_kwargs",
        },
        "IBM WatsonX": {
            "model_id": "model_id",
            "url": "url",
            "api_key": "apikey",
            "project_id": "project_id",
            "space_id": "space_id",
            "request_timeout": "request_timeout",
        },
    }

    # Track which providers have models
    providers_with_models = set()

    for provider_data in all_models:
        provider = provider_data.get("provider")
        if provider not in enabled_providers:
            continue

        models = provider_data.get("models", [])
        icon = provider_data.get("icon", "Bot")

        # Check if provider is enabled
        is_provider_enabled = not user_id or not enabled_providers or provider in enabled_providers

        # Track this provider
        if is_provider_enabled:
            providers_with_models.add(provider)

        # Skip provider if user_id is provided and provider is not enabled
        if user_id and enabled_providers and provider not in enabled_providers:
            continue

        for model_data in models:
            model_name = model_data.get("model_name")
            metadata = model_data.get("metadata", {})
            is_default = metadata.get("default", False)

            # Determine if model should be shown:
            # - If not default and not explicitly enabled, skip it
            # - If in disabled list, skip it
            # - Otherwise, show it
            if not is_default and model_name not in explicitly_enabled_models:
                continue
            if model_name in disabled_models:
                continue

            # Build the option dict
            option = {
                "name": model_name,
                "icon": icon,
                "category": provider,
                "provider": provider,
                "metadata": {
                    "embedding_class": EMBEDDING_PROVIDER_CLASS_MAPPING.get(provider, "OpenAIEmbeddings"),
                    "param_mapping": param_mappings.get(provider, param_mappings["OpenAI"]),
                    "model_type": "embeddings",  # Mark as embedding model
                },
            }

            options.append(option)

    return options