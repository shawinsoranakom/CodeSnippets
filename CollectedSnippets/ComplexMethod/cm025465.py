async def async_setup_entry(
    hass: HomeAssistant,
    entry: FluxLedConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the Flux selects."""
    coordinator = entry.runtime_data
    device = coordinator.device
    entities: list[
        FluxPowerStateSelect
        | FluxOperatingModesSelect
        | FluxWiringsSelect
        | FluxICTypeSelect
        | FluxRemoteConfigSelect
        | FluxWhiteChannelSelect
    ] = []
    entry.data.get(CONF_NAME, entry.title)
    base_unique_id = entry.unique_id or entry.entry_id

    if device.device_type == DeviceType.Switch:
        entities.append(FluxPowerStateSelect(coordinator.device, entry))
    if device.operating_modes:
        entities.append(
            FluxOperatingModesSelect(coordinator, base_unique_id, "operating_mode")
        )
    if device.wirings and device.wiring is not None:
        entities.append(FluxWiringsSelect(coordinator, base_unique_id, "wiring"))
    if device.ic_types:
        entities.append(FluxICTypeSelect(coordinator, base_unique_id, "ic_type"))
    if device.remote_config:
        entities.append(
            FluxRemoteConfigSelect(coordinator, base_unique_id, "remote_config")
        )
    if FLUX_COLOR_MODE_RGBW in device.color_modes:
        entities.append(FluxWhiteChannelSelect(coordinator.device, entry))

    async_add_entities(entities)