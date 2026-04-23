async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: HomematicIPConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the HomematicIP Cloud sensors from a config entry."""
    hap = config_entry.runtime_data
    entities: list[HomematicipGenericEntity] = []

    # Get device handlers dynamically
    device_handlers = get_device_handlers(hap)

    # Process all devices
    for device in hap.home.devices:
        for device_class, handler in device_handlers.items():
            if isinstance(device, device_class):
                entities.extend(handler(device))

    # Handle floor terminal blocks separately
    floor_terminal_blocks = (
        FloorTerminalBlock6,
        FloorTerminalBlock10,
        FloorTerminalBlock12,
        WiredFloorTerminalBlock12,
    )
    entities.extend(
        HomematicipFloorTerminalBlockMechanicChannelValve(
            hap, device, channel=channel.index
        )
        for device in hap.home.devices
        if isinstance(device, floor_terminal_blocks)
        for channel in device.functionalChannels
        if isinstance(channel, FloorTerminalBlockMechanicChannel)
        and getattr(channel, "valvePosition", None) is not None
    )

    # Handle smoke detector extended sensors (e.g., HmIP-SWSD-2)
    entities.extend(
        HmipSmokeDetectorSensor(hap, device, description)
        for device in hap.home.devices
        if isinstance(device, SmokeDetector)
        for description in SMOKE_DETECTOR_SENSORS
        if smoke_detector_channel_data_exists(device, description.channel_field)
    )

    async_add_entities(entities)