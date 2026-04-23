async def async_setup_entry(hass: HomeAssistant, entry: WithingsConfigEntry) -> bool:
    """Set up Withings from a config entry."""
    if CONF_WEBHOOK_ID not in entry.data or entry.unique_id is None:
        new_data = entry.data.copy()
        unique_id = str(entry.data[CONF_TOKEN]["userid"])
        if CONF_WEBHOOK_ID not in new_data:
            new_data[CONF_WEBHOOK_ID] = webhook_generate_id()

        hass.config_entries.async_update_entry(
            entry, data=new_data, unique_id=unique_id
        )
    session = async_get_clientsession(hass)
    client = WithingsClient(session=session)
    try:
        implementation = await async_get_config_entry_implementation(hass, entry)
    except ImplementationUnavailableError as err:
        raise ConfigEntryNotReady(
            translation_domain=DOMAIN,
            translation_key="oauth2_implementation_unavailable",
        ) from err
    oauth_session = OAuth2Session(hass, entry, implementation)

    refresh_lock = asyncio.Lock()

    async def _refresh_token() -> str:
        async with refresh_lock:
            await oauth_session.async_ensure_token_valid()
            token = oauth_session.token[CONF_ACCESS_TOKEN]
            if TYPE_CHECKING:
                assert isinstance(token, str)
            return token

    client.refresh_token_function = _refresh_token
    withings_data = WithingsData(
        client=client,
        measurement_coordinator=WithingsMeasurementDataUpdateCoordinator(
            hass, entry, client
        ),
        sleep_coordinator=WithingsSleepDataUpdateCoordinator(hass, entry, client),
        bed_presence_coordinator=WithingsBedPresenceDataUpdateCoordinator(
            hass, entry, client
        ),
        goals_coordinator=WithingsGoalsDataUpdateCoordinator(hass, entry, client),
        activity_coordinator=WithingsActivityDataUpdateCoordinator(hass, entry, client),
        workout_coordinator=WithingsWorkoutDataUpdateCoordinator(hass, entry, client),
        device_coordinator=WithingsDeviceDataUpdateCoordinator(hass, entry, client),
    )

    for coordinator in withings_data.coordinators:
        await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = withings_data

    webhook_manager = WithingsWebhookManager(hass, entry)

    async def manage_cloudhook(state: cloud.CloudConnectionState) -> None:
        LOGGER.debug("Cloudconnection state changed to %s", state)
        if state is cloud.CloudConnectionState.CLOUD_CONNECTED:
            await webhook_manager.register_webhook(None)

        if state is cloud.CloudConnectionState.CLOUD_DISCONNECTED:
            await webhook_manager.unregister_webhook(None)
            entry.async_on_unload(
                async_call_later(hass, 30, webhook_manager.register_webhook)
            )

    if cloud.async_active_subscription(hass):
        if cloud.async_is_connected(hass):
            entry.async_on_unload(
                async_call_later(
                    hass, WEBHOOK_REGISTER_DELAY, webhook_manager.register_webhook
                )
            )
        entry.async_on_unload(
            cloud.async_listen_connection_change(hass, manage_cloudhook)
        )
    else:
        entry.async_on_unload(
            async_call_later(
                hass, WEBHOOK_REGISTER_DELAY, webhook_manager.register_webhook
            )
        )

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True