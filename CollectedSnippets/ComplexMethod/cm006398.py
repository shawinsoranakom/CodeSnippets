async def _resolve_assistant_context(
    request: AssistantRequest,
    user_id: UUID,
    session: AsyncSession,
) -> _AssistantContext:
    """Resolve provider, model, API key, and build execution context.

    Raises:
        HTTPException: If provider is not configured or API key is missing.
    """
    provider_variable_map = get_model_provider_variable_mapping()
    enabled_providers, _ = await get_enabled_providers_for_user(user_id, session)

    if not enabled_providers:
        raise HTTPException(
            status_code=400,
            detail="No model provider is configured. Please configure at least one model provider in Settings.",
        )

    provider = request.provider
    if not provider:
        for preferred in PREFERRED_PROVIDERS:
            if preferred in enabled_providers:
                provider = preferred
                break
        if not provider:
            provider = enabled_providers[0]

    if provider not in enabled_providers:
        raise HTTPException(
            status_code=400,
            detail=f"Provider '{provider}' is not configured. Available providers: {enabled_providers}",
        )

    api_key_name = provider_variable_map.get(provider)
    if not api_key_name:
        raise HTTPException(status_code=400, detail=f"Unknown provider: {provider}")

    model_name = request.model_name or get_default_model(provider) or ""

    # Get all configured variables for the provider
    provider_vars = get_all_variables_for_provider(user_id, provider)

    # Validate all required variables are present
    required_keys = get_provider_required_variable_keys(provider)
    missing_keys = [key for key in required_keys if not provider_vars.get(key)]

    if missing_keys:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Missing required configuration for {provider}: {', '.join(missing_keys)}. "
                "Please configure these in Settings > Model Providers."
            ),
        )

    global_vars: dict[str, str] = {
        "USER_ID": str(user_id),
        "FLOW_ID": request.flow_id,
        "MODEL_NAME": model_name,
        "PROVIDER": provider,
    }

    # Inject all provider variables into the global context
    global_vars.update(provider_vars)

    session_id = request.session_id or str(uuid.uuid4())
    max_retries = request.max_retries if request.max_retries is not None else MAX_VALIDATION_RETRIES

    return _AssistantContext(
        provider=provider,
        model_name=model_name,
        api_key_name=api_key_name,
        session_id=session_id,
        global_vars=global_vars,
        max_retries=max_retries,
    )