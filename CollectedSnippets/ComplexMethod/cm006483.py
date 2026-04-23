async def get_enabled_models(
    *,
    session: DbSession,
    current_user: CurrentActiveUser,
    model_names: Annotated[list[str] | None, Query()] = None,
):
    """Get enabled models for the current user."""
    # Get all models - this returns a list of provider dicts with nested models
    all_models_by_provider = get_unified_models_detailed(
        include_unsupported=True,
        include_deprecated=True,
    )

    # Get enabled providers status
    enabled_providers_result = await get_enabled_providers(session=session, current_user=current_user)
    provider_status = enabled_providers_result.get("provider_status", {})

    # Replace static models with live models for providers that support it
    configured_providers = {p for p, configured in provider_status.items() if configured}
    replace_with_live_models(all_models_by_provider, current_user.id, configured_providers)

    # Get disabled and explicitly enabled models lists
    disabled_models = await _get_disabled_models(session=session, current_user=current_user)
    explicitly_enabled_models = await _get_enabled_models(session=session, current_user=current_user)

    # Build model status based on provider enablement
    enabled_models: dict[str, dict[str, bool]] = {}

    # Iterate through providers and their models
    for provider_dict in all_models_by_provider:
        provider = provider_dict.get("provider")
        models = provider_dict.get("models", [])

        # Initialize provider dict if not exists
        if provider not in enabled_models:
            enabled_models[provider] = {}

        for model in models:
            model_name = model.get("model_name")
            metadata = model.get("metadata", {})

            # Check if model is deprecated or not supported
            is_deprecated = metadata.get("deprecated", False)
            is_not_supported = metadata.get("not_supported", False)
            is_default = metadata.get("default", False)

            # Model is enabled if:
            # 1. Provider is enabled
            # 2. Model is not deprecated/unsupported
            # 3. Model is either:
            #    - Marked as default (default=True), OR
            #    - Explicitly enabled by user (in explicitly_enabled_models), AND
            #    - NOT explicitly disabled by user (not in disabled_models)
            is_enabled = (
                provider_status.get(provider, False)
                and not is_deprecated
                and not is_not_supported
                and (is_default or model_name in explicitly_enabled_models)
                and model_name not in disabled_models
            )
            # Store model status per provider (true/false)
            enabled_models[provider][model_name] = is_enabled

    result = {
        "enabled_models": enabled_models,
    }

    if model_names:
        # Filter enabled_models by requested models
        filtered_enabled: dict[str, dict[str, bool]] = {}
        for provider, models_dict in enabled_models.items():
            filtered_models = {m: v for m, v in models_dict.items() if m in model_names}
            if filtered_models:
                filtered_enabled[provider] = filtered_models
        return {
            "enabled_models": filtered_enabled,
        }

    return result