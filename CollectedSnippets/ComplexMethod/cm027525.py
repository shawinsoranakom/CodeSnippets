async def async_setup_entry(
    hass: HomeAssistant,
    entry: SmartThingsConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Add number entities for a config entry."""
    entry_data = entry.runtime_data
    entities: list[NumberEntity] = [
        SmartThingsWasherRinseCyclesNumberEntity(entry_data.client, device)
        for device in entry_data.devices.values()
        if Capability.CUSTOM_WASHER_RINSE_CYCLES in device.status[MAIN]
    ]
    entities.extend(
        SmartThingsHoodNumberEntity(entry_data.client, device)
        for device in entry_data.devices.values()
        if (
            (hood_component := device.status.get("hood")) is not None
            and Capability.SAMSUNG_CE_HOOD_FAN_SPEED in hood_component
            and Capability.SAMSUNG_CE_CONNECTION_STATE not in hood_component
        )
    )
    entities.extend(
        SmartThingsRefrigeratorTemperatureNumberEntity(
            entry_data.client, device, component
        )
        for device in entry_data.devices.values()
        for component in device.status
        if component in ("cooler", "freezer", "onedoor")
        and Capability.THERMOSTAT_COOLING_SETPOINT in device.status[component]
        and device.status[component][Capability.THERMOSTAT_COOLING_SETPOINT][
            Attribute.COOLING_SETPOINT_RANGE
        ].value
        is not None
    )
    async_add_entities(entities)