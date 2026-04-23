async def async_setup_entry(hass: HomeAssistant, entry: LoJackConfigEntry) -> bool:
    """Set up LoJack from a config entry."""
    session = async_get_clientsession(hass)

    try:
        client = await LoJackClient.create(
            entry.data[CONF_USERNAME],
            entry.data[CONF_PASSWORD],
            session=session,
        )
    except AuthenticationError as err:
        raise ConfigEntryAuthFailed(f"Authentication failed: {err}") from err
    except ApiError as err:
        raise ConfigEntryNotReady(f"API error during setup: {err}") from err

    try:
        vehicles = await client.list_devices()
    except AuthenticationError as err:
        await client.close()
        raise ConfigEntryAuthFailed(f"Authentication failed: {err}") from err
    except ApiError as err:
        await client.close()
        raise ConfigEntryNotReady(f"API error during setup: {err}") from err

    data = LoJackData(client=client)
    entry.runtime_data = data

    try:
        for vehicle in vehicles or []:
            if isinstance(vehicle, Vehicle):
                coordinator = LoJackCoordinator(hass, client, entry, vehicle)
                await coordinator.async_config_entry_first_refresh()
                data.coordinators.append(coordinator)
    except Exception:
        await client.close()
        raise

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True