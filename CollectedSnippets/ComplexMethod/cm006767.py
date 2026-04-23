def get_language_model_options(
    user_id: UUID | str | None = None, *, tool_calling: bool | None = None
) -> list[dict[str, Any]]:
    """Return available language model providers with their configuration."""
    # Get all LLM models (excluding embeddings, deprecated, and unsupported by default)
    # Apply tool_calling filter if specified
    if tool_calling is not None:
        all_models = get_unified_models_detailed(
            model_type="llm",
            include_deprecated=False,
            include_unsupported=False,
            tool_calling=tool_calling,
        )
    else:
        all_models = get_unified_models_detailed(
            model_type="llm",
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
        replace_with_live_models(all_models, user_id, enabled_providers, "llm", model_provider_metadata)

    options = []

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

            # Get parameter mapping for this provider
            param_mapping = get_provider_param_mapping(provider)

            # Build the option dict
            # Get provider-level metadata for max_tokens field name
            provider_meta = model_provider_metadata.get(provider, {})
            option_metadata = {
                "context_length": 128000,  # Default, can be overridden
                "model_class": param_mapping.get("model_class", "ChatOpenAI"),
                "model_name_param": param_mapping.get("model_param", "model"),
                "api_key_param": param_mapping.get("api_key_param", "api_key"),
            }
            if "max_tokens_field_name" in provider_meta:
                option_metadata["max_tokens_field_name"] = provider_meta["max_tokens_field_name"]

            option = {
                "name": model_name,
                "icon": icon,
                "category": provider,
                "provider": provider,
                "metadata": option_metadata,
            }

            # Add reasoning models list for OpenAI
            if provider == "OpenAI" and metadata.get("reasoning"):
                if "reasoning_models" not in option["metadata"]:
                    option["metadata"]["reasoning_models"] = []
                option["metadata"]["reasoning_models"].append(model_name)

            # Add provider-specific params from mapping
            if "base_url_param" in param_mapping:
                option["metadata"]["base_url_param"] = param_mapping["base_url_param"]
            if "url_param" in param_mapping:
                option["metadata"]["url_param"] = param_mapping["url_param"]
            if "project_id_param" in param_mapping:
                option["metadata"]["project_id_param"] = param_mapping["project_id_param"]

            options.append(option)

    return options