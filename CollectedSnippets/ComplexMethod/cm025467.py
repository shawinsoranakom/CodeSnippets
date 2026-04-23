async def async_setup_entry(hass: HomeAssistant, entry: FluxLedConfigEntry) -> bool:
    """Set up Flux LED/MagicLight from a config entry."""
    host = entry.data[CONF_HOST]
    discovery_cached = True
    if discovery := async_get_discovery(hass, host):
        discovery_cached = False
    else:
        discovery = async_build_cached_discovery(entry)
    device: AIOWifiLedBulb = async_wifi_bulb_for_host(host, discovery=discovery)
    signal = SIGNAL_STATE_UPDATED.format(device.ipaddr)
    device.discovery = discovery
    if white_channel_type := entry.data.get(CONF_WHITE_CHANNEL_TYPE):
        device.white_channel_channel_type = NAME_TO_WHITE_CHANNEL_TYPE[
            white_channel_type
        ]

    @callback
    def _async_state_changed(*_: Any) -> None:
        _LOGGER.debug("%s: Device state updated: %s", device.ipaddr, device.raw_state)
        async_dispatcher_send(hass, signal)

    try:
        await device.async_setup(_async_state_changed)
    except FLUX_LED_EXCEPTIONS as ex:
        raise ConfigEntryNotReady(
            str(ex) or f"Timed out trying to connect to {device.ipaddr}"
        ) from ex

    # UDP probe after successful connect only
    if discovery_cached:
        if directed_discovery := await async_discover_device(hass, host):
            device.discovery = discovery = directed_discovery
            discovery_cached = False

    if entry.unique_id and discovery.get(ATTR_ID):
        mac = dr.format_mac(cast(str, discovery[ATTR_ID]))
        if not mac_matches_by_one(mac, entry.unique_id):
            # The device is offline and another flux_led device is now using the ip address
            raise ConfigEntryNotReady(
                f"Unexpected device found at {host}; Expected {entry.unique_id}, found"
                f" {mac}"
            )

    if not discovery_cached:
        # Only update the entry once we have verified the unique id
        # is either missing or we have verified it matches
        async_update_entry_from_discovery(
            hass, entry, discovery, device.model_num, True
        )

    await _async_migrate_unique_ids(hass, entry)

    coordinator = FluxLedUpdateCoordinator(hass, device, entry)
    entry.runtime_data = coordinator
    platforms = PLATFORMS_BY_TYPE[device.device_type]
    await hass.config_entries.async_forward_entry_setups(entry, platforms)

    async def _async_sync_time(*args: Any) -> None:
        """Set the time every morning at 02:40:30."""
        await device.async_set_time()

    await _async_sync_time()  # set at startup
    entry.async_on_unload(async_track_time_change(hass, _async_sync_time, 3, 40, 30))

    # There must not be any awaits between here and the return
    # to avoid a race condition where the add_update_listener is not
    # in place in time for the check in async_update_entry_from_discovery
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))

    async def _async_handle_discovered_device() -> None:
        """Handle device discovery."""
        # Force a refresh if the device is now available
        if not coordinator.last_update_success:
            coordinator.force_next_update = True
            await coordinator.async_refresh()

    entry.async_on_unload(
        async_dispatcher_connect(
            hass,
            FLUX_LED_DISCOVERY_SIGNAL.format(entry_id=entry.entry_id),
            _async_handle_discovered_device,
        )
    )
    return True