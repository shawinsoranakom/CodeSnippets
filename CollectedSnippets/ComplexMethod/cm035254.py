async def load_settings(
    provider_tokens: PROVIDER_TOKEN_TYPE | None = Depends(get_provider_tokens),
    settings_store: SettingsStore = Depends(get_user_settings_store),
    settings: Settings = Depends(get_user_settings),
    secrets_store: SecretsStore = Depends(get_secrets_store),
) -> GETSettingsModel | JSONResponse:
    """Load user settings.

    Retrieves the settings for the authenticated user, including LLM configuration,
    provider tokens, and other user preferences.

    Returns:
        GETSettingsModel: The user settings with token data

    Raises:
        404: Settings not found
        401: Invalid token
    """
    try:
        if not settings:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={'error': 'Settings not found'},
            )

        # On initial load, user secrets may not be populated with values migrated from settings store
        user_secrets = await invalidate_legacy_secrets_store(
            settings, settings_store, secrets_store
        )

        # If invalidation is successful, then the returned user secrets holds the most recent values
        git_providers = (
            user_secrets.provider_tokens if user_secrets else provider_tokens
        )

        provider_tokens_set: dict[ProviderType, str | None] = {}
        if git_providers:
            for provider_type, provider_token in git_providers.items():
                if provider_token.token or provider_token.user_id:
                    provider_tokens_set[provider_type] = provider_token.host

        llm = settings.agent_settings.llm
        settings_with_token_data = GETSettingsModel(
            **settings.model_dump(exclude={'secrets_store'}),
            llm_api_key_set=settings.llm_api_key_is_set,
            search_api_key_set=settings.search_api_key is not None
            and bool(settings.search_api_key),
            provider_tokens_set=provider_tokens_set,
        )

        # Convert litellm_proxy/ back to openhands/ for the frontend
        resp_llm = settings_with_token_data.agent_settings.llm
        if resp_llm.model and resp_llm.model.startswith('litellm_proxy/'):
            resp_llm.model = (
                f'openhands/{resp_llm.model.removeprefix("litellm_proxy/")}'
            )

        # If the base url matches the default for the provider, we don't send it
        # So that the frontend can display basic mode.
        # Normalize trailing slashes for comparison since the SDK may add one.
        normalized_base = (llm.base_url or '').rstrip('/')
        normalized_proxy = LITE_LLM_API_URL.rstrip('/')
        if is_openhands_model(llm.model):
            if normalized_base == normalized_proxy:
                resp_llm.base_url = None
        elif llm.model and llm.base_url == get_provider_api_base(llm.model):
            resp_llm.base_url = None

        resp_llm.api_key = None
        settings_with_token_data.search_api_key = None
        settings_with_token_data.sandbox_api_key = None
        return settings_with_token_data
    except Exception as e:
        logger.warning(f'Invalid token: {e}')
        # Get user_id from settings if available
        user_id = getattr(settings, 'user_id', 'unknown') if settings else 'unknown'
        logger.info(
            f'Returning 401 Unauthorized - Invalid token for user_id: {user_id}'
        )
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={'error': 'Invalid token'},
        )