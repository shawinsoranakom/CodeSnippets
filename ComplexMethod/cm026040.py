async def async_setup_entry(hass: HomeAssistant, entry: InComfortConfigEntry) -> bool:
    """Set up a config entry."""
    try:
        data = await async_connect_gateway(hass, dict(entry.data))
        for heater in data.heaters:
            await heater.update()
    except InvalidHeaterList as exc:
        raise NoHeaters from exc
    except InvalidGateway as exc:
        raise ConfigEntryAuthFailed("Incorrect credentials") from exc
    except ClientResponseError as exc:
        if exc.status == 404:
            raise NotFound from exc
        raise InComfortUnknownError from exc
    except TimeoutError as exc:
        raise InComfortTimeout from exc

    # Register discovered gateway device
    device_registry = dr.async_get(hass)
    gateway_device = device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, entry.entry_id)},
        connections={(dr.CONNECTION_NETWORK_MAC, entry.unique_id)}
        if entry.unique_id is not None
        else set(),
        manufacturer="Intergas",
        name="RFGateway",
    )
    async_cleanup_stale_devices(hass, entry, data, gateway_device)
    coordinator = InComfortDataCoordinator(hass, entry, data)
    entry.runtime_data = coordinator
    await coordinator.async_config_entry_first_refresh()

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True