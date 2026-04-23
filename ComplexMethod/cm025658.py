async def async_setup_entry(hass: HomeAssistant, entry: MelCloudConfigEntry) -> bool:
    """Establish connection with MELCloud."""
    try:
        async with asyncio.timeout(10):
            all_devices = await get_devices(
                token=entry.data[CONF_TOKEN],
                session=async_get_clientsession(hass),
                conf_update_interval=timedelta(minutes=30),
                device_set_debounce=timedelta(seconds=2),
            )
    except ClientResponseError as ex:
        if ex.status in (HTTPStatus.UNAUTHORIZED, HTTPStatus.FORBIDDEN):
            raise ConfigEntryAuthFailed from ex
        if ex.status == HTTPStatus.TOO_MANY_REQUESTS:
            raise UpdateFailed(
                "MELCloud rate limit exceeded. Your account may be temporarily blocked"
            ) from ex
        raise UpdateFailed(f"Error communicating with MELCloud: {ex}") from ex
    except (TimeoutError, ClientConnectionError) as ex:
        raise UpdateFailed(f"Error communicating with MELCloud: {ex}") from ex

    # Create per-device coordinators
    coordinators: dict[str, list[MelCloudDeviceUpdateCoordinator]] = {}
    device_registry = dr.async_get(hass)
    for device_type, devices in all_devices.items():
        # Build coordinators for this device_type
        coordinators[device_type] = [
            MelCloudDeviceUpdateCoordinator(hass, device, entry) for device in devices
        ]

        # Perform initial refreshes concurrently
        await asyncio.gather(
            *(
                coordinator.async_config_entry_first_refresh()
                for coordinator in coordinators[device_type]
            )
        )

        # Register parent devices so zone entities can reference via_device
        for coordinator in coordinators[device_type]:
            device_registry.async_get_or_create(
                config_entry_id=entry.entry_id,
                **coordinator.device_info,
            )

    entry.runtime_data = coordinators
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True