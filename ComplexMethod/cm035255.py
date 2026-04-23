async def store_settings(
    payload: dict[str, Any],
    settings_store: SettingsStore = Depends(get_user_settings_store),
) -> JSONResponse:
    """Store user settings.

    Accepts a partial payload and deep-merges ``agent_settings_diff`` and
    ``conversation_settings_diff`` with the existing persisted values so that
    saving one settings page never overwrites fields owned by another.

    Returns:
        200: Settings stored successfully
        422: Legacy nested settings keys are rejected
        500: Error storing settings
    """
    legacy_nested_keys = sorted(
        key for key in ('agent_settings', 'conversation_settings') if key in payload
    )
    if legacy_nested_keys:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            content={
                'error': 'Use *_diff nested settings payloads instead of legacy keys',
                'keys': legacy_nested_keys,
            },
        )

    try:
        existing_settings = await settings_store.load()
        settings = existing_settings.model_copy() if existing_settings else Settings()
        settings.update(payload)

        _post_merge_llm_fixups(settings)

        if existing_settings:
            if 'search_api_key' not in payload and settings.search_api_key is None:
                settings.search_api_key = existing_settings.search_api_key
            if settings.user_consents_to_analytics is None:
                settings.user_consents_to_analytics = (
                    existing_settings.user_consents_to_analytics
                )
            if settings.disabled_skills is None:
                settings.disabled_skills = existing_settings.disabled_skills

        # Update sandbox config with new settings
        if settings.remote_runtime_resource_factor is not None:
            config.sandbox.remote_runtime_resource_factor = (
                settings.remote_runtime_resource_factor
            )

        # Update git configuration with new settings
        git_config_updated = False
        if settings.git_user_name is not None:
            config.git_user_name = settings.git_user_name
            git_config_updated = True
        if settings.git_user_email is not None:
            config.git_user_email = settings.git_user_email
            git_config_updated = True

        if git_config_updated:
            logger.info(
                f'Updated global git configuration: name={config.git_user_name}, email={config.git_user_email}'
            )

        await settings_store.store(settings)
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={'message': 'Settings stored'},
        )
    except Exception as e:
        logger.warning(f'Something went wrong storing settings: {e}')
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={'error': 'Something went wrong storing settings'},
        )