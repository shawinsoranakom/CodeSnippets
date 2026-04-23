async def async_setup_entry(hass: HomeAssistant, entry: TibberConfigEntry) -> bool:
    """Set up a config entry."""

    # Added in 2026.1 to migrate existing users to OAuth2 (Tibber Data API).
    # Can be removed after 2026.7
    if AUTH_IMPLEMENTATION not in entry.data:
        raise ConfigEntryAuthFailed(
            translation_domain=DOMAIN,
            translation_key="data_api_reauth_required",
        )

    try:
        implementation = await async_get_config_entry_implementation(hass, entry)
    except ImplementationUnavailableError as err:
        raise ConfigEntryNotReady(
            translation_domain=DOMAIN,
            translation_key="oauth2_implementation_unavailable",
        ) from err

    session = OAuth2Session(hass, entry, implementation)
    try:
        await session.async_ensure_token_valid()
    except ClientResponseError as err:
        if 400 <= err.status < 500:
            raise ConfigEntryAuthFailed(
                "OAuth session is not valid, reauthentication required"
            ) from err
        raise ConfigEntryNotReady from err
    except ClientError as err:
        raise ConfigEntryNotReady from err

    entry.runtime_data = TibberRuntimeData(
        session=session,
    )

    tibber_connection = await entry.runtime_data.async_get_client(hass)

    async def _close(event: Event) -> None:
        await tibber_connection.rt_disconnect()

    entry.async_on_unload(hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, _close))

    try:
        await tibber_connection.update_info()
    except (
        TimeoutError,
        aiohttp.ClientError,
        tibber.RetryableHttpExceptionError,
    ) as err:
        raise ConfigEntryNotReady("Unable to connect") from err
    except tibber.InvalidLoginError as err:
        raise ConfigEntryAuthFailed("Invalid login credentials") from err
    except tibber.FatalHttpExceptionError as err:
        raise ConfigEntryNotReady("Fatal HTTP error from Tibber API") from err

    if tibber_connection.get_homes(only_active=True):
        price_coordinator = TibberPriceCoordinator(hass, entry)
        await price_coordinator.async_config_entry_first_refresh()
        entry.runtime_data.price_coordinator = price_coordinator

        data_coordinator = TibberDataCoordinator(hass, entry, tibber_connection)
        await data_coordinator.async_config_entry_first_refresh()
        entry.runtime_data.data_coordinator = data_coordinator

    coordinator = TibberDataAPICoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data.data_api_coordinator = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True