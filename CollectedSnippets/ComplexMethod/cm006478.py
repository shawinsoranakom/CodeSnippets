async def list_models(
    *,
    provider: Annotated[list[str] | None, Query(description="Repeat to include multiple providers")] = None,
    model_name: str | None = None,
    model_type: str | None = None,
    include_unsupported: bool = False,
    include_deprecated: bool = False,
    # common metadata filters
    tool_calling: bool | None = None,
    reasoning: bool | None = None,
    search: bool | None = None,
    preview: bool | None = None,
    deprecated: bool | None = None,
    not_supported: bool | None = None,
    session: DbSession,
    current_user: CurrentActiveUser,
):
    """Return model catalog filtered by query parameters.

    Pass providers as repeated query params, e.g. `?provider=OpenAI&provider=Anthropic`.
    """
    selected_providers: list[str] | None = provider
    metadata_filters = {
        k: v
        for k, v in {
            "tool_calling": tool_calling,
            "reasoning": reasoning,
            "search": search,
            "preview": preview,
            "deprecated": deprecated,
            "not_supported": not_supported,
        }.items()
        if v is not None
    }

    # Get enabled providers status (now just checks if variables exist)
    enabled_providers_result = await get_enabled_providers(session=session, current_user=current_user)
    provider_configured_status = enabled_providers_result.get("provider_status", {})

    # Get enabled models map for current user to determine "active" providers
    enabled_models_result = await get_enabled_models(session=session, current_user=current_user)
    enabled_models_map = enabled_models_result.get("enabled_models", {})

    # Get default model if model_type is specified
    default_provider = None
    if model_type:
        try:
            default_model_result = await get_default_model(
                session=session, current_user=current_user, model_type=model_type
            )
            if default_model_result.get("default_model"):
                default_provider = default_model_result["default_model"].get("provider")
        except Exception:  # noqa: BLE001
            # Default model fetch failed, continue without it
            # This is not critical for the main operation - we suppress to avoid breaking the list
            logger.debug("Failed to fetch default model, continuing without it", exc_info=True)

    # Get filtered models - pass providers directly to avoid filtering after
    filtered_models = get_unified_models_detailed(
        providers=selected_providers,
        model_name=model_name,
        include_unsupported=include_unsupported,
        include_deprecated=include_deprecated,
        model_type=model_type,
        **metadata_filters,
    )

    # Add configured and enabled status to each provider
    for provider_dict in filtered_models:
        prov_name = provider_dict.get("provider")
        provider_dict["is_configured"] = provider_configured_status.get(prov_name, False)

        # Provider is "enabled" (active) if it has at least one enabled model
        prov_models_status = enabled_models_map.get(prov_name, {})
        has_active_model = any(prov_models_status.values())
        provider_dict["is_enabled"] = has_active_model

    # Replace static models with live models for providers that support it
    configured_providers = {p for p, configured in provider_configured_status.items() if configured}
    replace_with_live_models(filtered_models, current_user.id, configured_providers, model_type)

    # Sort providers:
    # 1. Provider with default model first
    # 2. Configured providers next
    # 3. Alphabetically after that
    def sort_key(provider_dict):
        provider_name = provider_dict.get("provider", "")
        # Use is_configured for sorting priority (so they appear at top when ready)
        is_configured = provider_dict.get("is_configured", False)
        is_default = provider_name == default_provider

        # Return tuple for sorting: (not is_default, not is_configured, provider_name)
        # This way default comes first (False < True), then configured, then alphabetical
        return (not is_default, not is_configured, provider_name)

    filtered_models.sort(key=sort_key)

    return filtered_models