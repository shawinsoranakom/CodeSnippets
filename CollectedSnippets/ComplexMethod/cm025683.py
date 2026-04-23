async def _async_update_profile(call: ServiceCall) -> ServiceResponse:
    """Update profile information."""
    params = dict(call.data.copy())

    entry: MastodonConfigEntry = service.async_get_config_entry(
        call.hass, DOMAIN, params.pop(ATTR_CONFIG_ENTRY_ID)
    )
    client = entry.runtime_data.client

    if avatar := params.pop(ATTR_AVATAR, None):
        params[ATTR_AVATAR], params[ATTR_AVATAR_MIME_TYPE] = await _resolve_media(
            call.hass, avatar
        )
    if header := params.pop(ATTR_HEADER, None):
        params[ATTR_HEADER], params[ATTR_HEADER_MIME_TYPE] = await _resolve_media(
            call.hass, header
        )
    if fields := params.get(ATTR_FIELDS):
        params[ATTR_FIELDS] = [
            (field[ATTR_NAME].strip(), field[ATTR_VALUE].strip())
            for field in fields
            if field[ATTR_NAME].strip()
        ]
    try:
        return await call.hass.async_add_executor_job(
            lambda: client.account_update_credentials(**params)
        )
    except MastodonUnauthorizedError as error:
        entry.async_start_reauth(call.hass)
        raise HomeAssistantError(
            translation_domain=DOMAIN,
            translation_key="auth_failed",
        ) from error
    except MastodonAPIError as err:
        LOGGER.debug("Full exception:", exc_info=err)
        raise HomeAssistantError(
            translation_domain=DOMAIN,
            translation_key="unable_to_update_profile",
        ) from err