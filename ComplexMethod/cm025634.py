async def async_setup_entry(hass: HomeAssistant, entry: GoogleConfigEntry) -> bool:
    """Set up Google from a config entry."""
    # Validate google_calendars.yaml (if present) as soon as possible to return
    # helpful error messages.
    try:
        await hass.async_add_executor_job(load_config, hass.config.path(YAML_DEVICES))
    except vol.Invalid as err:
        _LOGGER.error("Configuration error in %s: %s", YAML_DEVICES, str(err))
        return False

    try:
        implementation = (
            await config_entry_oauth2_flow.async_get_config_entry_implementation(
                hass, entry
            )
        )
    except ImplementationUnavailableError as err:
        raise ConfigEntryNotReady(
            translation_domain=DOMAIN,
            translation_key="oauth2_implementation_unavailable",
        ) from err
    session = config_entry_oauth2_flow.OAuth2Session(hass, entry, implementation)
    # Force a token refresh to fix a bug where tokens were persisted with
    # expires_in (relative time delta) and expires_at (absolute time) swapped.
    # A google session token typically only lasts a few days between refresh.
    now = datetime.now()
    if session.token["expires_at"] >= (now + timedelta(days=365)).timestamp():
        session.token["expires_in"] = 0
        session.token["expires_at"] = now.timestamp()
    try:
        await session.async_ensure_token_valid()
    except aiohttp.ClientResponseError as err:
        if 400 <= err.status < 500:
            raise ConfigEntryAuthFailed from err
        raise ConfigEntryNotReady from err
    except aiohttp.ClientError as err:
        raise ConfigEntryNotReady from err

    if not async_entry_has_scopes(entry):
        raise ConfigEntryAuthFailed(
            "Required scopes are not available, reauth required"
        )
    calendar_service = GoogleCalendarService(
        ApiAuthImpl(async_get_clientsession(hass), session)
    )
    entry.runtime_data = GoogleRuntimeData(
        service=calendar_service,
        store=LocalCalendarStore(hass, entry.entry_id),
    )

    if entry.unique_id is None:
        try:
            primary_calendar = await calendar_service.async_get_calendar("primary")
        except AuthException as err:
            raise ConfigEntryAuthFailed from err
        except ApiException as err:
            raise ConfigEntryNotReady from err

        hass.config_entries.async_update_entry(entry, unique_id=primary_calendar.id)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True