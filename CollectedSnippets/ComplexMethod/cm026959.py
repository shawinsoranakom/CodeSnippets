async def client_listen(
    hass: HomeAssistant,
    entry: ZwaveJSConfigEntry,
    client: ZwaveClient,
    driver_ready: asyncio.Event,
) -> None:
    """Listen with the client."""
    try:
        await client.listen(driver_ready)
    except BaseZwaveJSServerError as err:
        if entry.state is ConfigEntryState.SETUP_IN_PROGRESS:
            raise
        LOGGER.error("Client listen failed: %s", err)
    except Exception as err:
        # We need to guard against unknown exceptions to not crash this task.
        LOGGER.exception("Unexpected exception: %s", err)
        if entry.state is ConfigEntryState.SETUP_IN_PROGRESS:
            raise

    if hass.is_stopping or entry.state is ConfigEntryState.UNLOAD_IN_PROGRESS:
        return

    if entry.state is ConfigEntryState.SETUP_IN_PROGRESS:
        raise HomeAssistantError("Listen task ended unexpectedly")

    # The entry needs to be reloaded since a new driver state
    # will be acquired on reconnect.
    # All model instances will be replaced when the new state is acquired.
    if entry.state.recoverable:
        LOGGER.debug("Disconnected from server. Reloading integration")
        hass.config_entries.async_schedule_reload(entry.entry_id)
    else:
        LOGGER.error(
            "Disconnected from server. Cannot recover entry %s",
            entry.title,
        )