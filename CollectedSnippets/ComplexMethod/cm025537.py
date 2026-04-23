async def async_setup_entry(hass: HomeAssistant, entry: SleepIQConfigEntry) -> bool:
    """Set up the SleepIQ config entry."""
    conf = entry.data
    email = conf[CONF_USERNAME]
    password = conf[CONF_PASSWORD]

    client_session = async_get_clientsession(hass)

    gateway = AsyncSleepIQ(client_session=client_session)

    try:
        await gateway.login(email, password)
    except SleepIQLoginException as err:
        _LOGGER.error("Could not authenticate with SleepIQ server")
        raise ConfigEntryAuthFailed(err) from err
    except SleepIQTimeoutException as err:
        raise ConfigEntryNotReady(
            str(err) or "Timed out during authentication"
        ) from err

    try:
        await gateway.init_beds()
    except SleepIQTimeoutException as err:
        raise ConfigEntryNotReady(
            str(err) or "Timed out during initialization"
        ) from err
    except SleepIQAPIException as err:
        raise ConfigEntryNotReady(str(err) or "Error reading from SleepIQ API") from err

    await _async_migrate_unique_ids(hass, entry, gateway)

    coordinator = SleepIQDataUpdateCoordinator(hass, entry, gateway)
    pause_coordinator = SleepIQPauseUpdateCoordinator(hass, entry, gateway)
    sleep_data_coordinator = SleepIQSleepDataCoordinator(hass, entry, gateway)

    # Call the SleepIQ API to refresh data
    await coordinator.async_config_entry_first_refresh()
    await pause_coordinator.async_config_entry_first_refresh()
    await sleep_data_coordinator.async_config_entry_first_refresh()

    entry.runtime_data = SleepIQData(
        data_coordinator=coordinator,
        pause_coordinator=pause_coordinator,
        sleep_data_coordinator=sleep_data_coordinator,
        client=gateway,
    )

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True