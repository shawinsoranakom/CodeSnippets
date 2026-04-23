async def async_setup_entry(
    hass: HomeAssistant,
    entry: SmartThingsConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Add lights for a config entry."""
    entry_data = entry.runtime_data
    entities: list[LightEntity] = [
        SmartThingsLight(entry_data.client, device, component)
        for device in entry_data.devices.values()
        for component in device.status
        if (
            Capability.SWITCH in device.status[MAIN]
            and any(capability in device.status[MAIN] for capability in CAPABILITIES)
            and Capability.SAMSUNG_CE_LAMP not in device.status[component]
        )
    ]
    entities.extend(
        SmartThingsLamp(entry_data.client, device, component)
        for device in entry_data.devices.values()
        for component, exists_fn in LAMP_CAPABILITY_EXISTS.items()
        if component in device.status
        and Capability.SAMSUNG_CE_LAMP in device.status[component]
        and exists_fn(device, device.status[component])
    )
    async_add_entities(entities)