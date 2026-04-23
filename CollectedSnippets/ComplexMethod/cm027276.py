async def async_setup_entry(hass: HomeAssistant, entry: SENZConfigEntry) -> bool:
    """Set up SENZ from a config entry."""
    try:
        implementation = await async_get_config_entry_implementation(hass, entry)
    except ImplementationUnavailableError as err:
        raise ConfigEntryNotReady(
            translation_domain=DOMAIN,
            translation_key="oauth2_implementation_unavailable",
        ) from err
    session = OAuth2Session(hass, entry, implementation)
    auth = SENZConfigEntryAuth(httpx_client.get_async_client(hass), session)
    senz_api = SENZAPI(auth)

    try:
        account = await senz_api.get_account()
    except HTTPStatusError as err:
        if err.response.status_code == HTTPStatus.UNAUTHORIZED:
            raise ConfigEntryAuthFailed(
                translation_domain=DOMAIN,
                translation_key="config_entry_auth_failed",
            ) from err
        raise ConfigEntryNotReady(
            translation_domain=DOMAIN,
            translation_key="config_entry_not_ready",
        ) from err
    except ClientResponseError as err:
        if err.status in (HTTPStatus.UNAUTHORIZED, HTTPStatus.BAD_REQUEST):
            raise ConfigEntryAuthFailed(
                translation_domain=DOMAIN,
                translation_key="config_entry_auth_failed",
            ) from err
        raise ConfigEntryNotReady(
            translation_domain=DOMAIN,
            translation_key="config_entry_not_ready",
        ) from err
    except RequestError as err:
        raise ConfigEntryNotReady(
            translation_domain=DOMAIN,
            translation_key="config_entry_not_ready",
        ) from err
    except Exception as err:
        raise ConfigEntryAuthFailed(
            translation_domain=DOMAIN,
            translation_key="config_entry_auth_failed",
        ) from err

    coordinator = SENZDataUpdateCoordinator(
        hass,
        entry,
        name=account.username,
        senz_api=senz_api,
    )

    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True