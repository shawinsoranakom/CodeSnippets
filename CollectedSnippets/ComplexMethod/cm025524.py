async def async_setup_entry(
    hass: HomeAssistant, entry: DevoloHomeNetworkConfigEntry
) -> bool:
    """Set up devolo Home Network from a config entry."""
    zeroconf_instance = await zeroconf.async_get_async_instance(hass)
    async_client = get_async_client(hass)

    try:
        device = Device(
            ip=entry.data[CONF_IP_ADDRESS], zeroconf_instance=zeroconf_instance
        )
        await device.async_connect(session_instance=async_client)
        device.password = entry.data.get(
            CONF_PASSWORD,
            "",  # This key was added in HA Core 2022.6
        )
    except DeviceNotFound as err:
        raise ConfigEntryNotReady(
            translation_domain=DOMAIN,
            translation_key="connection_failed",
            translation_placeholders={"ip_address": entry.data[CONF_IP_ADDRESS]},
        ) from err

    entry.runtime_data = DevoloHomeNetworkData(device=device, coordinators={})

    async def disconnect(event: Event) -> None:
        """Disconnect from device."""
        await device.async_disconnect()

    coordinators: dict[str, DevoloDataUpdateCoordinator[Any]] = {}
    if device.plcnet:
        coordinators[CONNECTED_PLC_DEVICES] = DevoloLogicalNetworkCoordinator(
            hass,
            _LOGGER,
            config_entry=entry,
        )
    if device.device and "led" in device.device.features:
        coordinators[SWITCH_LEDS] = DevoloLedSettingsGetCoordinator(
            hass,
            _LOGGER,
            config_entry=entry,
        )
    if device.device and "restart" in device.device.features:
        coordinators[LAST_RESTART] = DevoloUptimeGetCoordinator(
            hass,
            _LOGGER,
            config_entry=entry,
        )
    if device.device and "update" in device.device.features:
        coordinators[REGULAR_FIRMWARE] = DevoloFirmwareUpdateCoordinator(
            hass,
            _LOGGER,
            config_entry=entry,
        )
    if device.device and "wifi1" in device.device.features:
        coordinators[CONNECTED_WIFI_CLIENTS] = (
            DevoloWifiConnectedStationsGetCoordinator(
                hass,
                _LOGGER,
                config_entry=entry,
            )
        )
        coordinators[NEIGHBORING_WIFI_NETWORKS] = DevoloWifiNeighborAPsGetCoordinator(
            hass,
            _LOGGER,
            config_entry=entry,
        )
        coordinators[SWITCH_GUEST_WIFI] = DevoloWifiGuestAccessGetCoordinator(
            hass,
            _LOGGER,
            config_entry=entry,
        )

    for coordinator in coordinators.values():
        await coordinator.async_config_entry_first_refresh()

    entry.runtime_data.coordinators = coordinators

    await hass.config_entries.async_forward_entry_setups(entry, platforms(device))

    entry.async_on_unload(
        hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, disconnect)
    )

    return True