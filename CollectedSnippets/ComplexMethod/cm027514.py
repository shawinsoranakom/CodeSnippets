async def async_setup_entry(
    hass: HomeAssistant,
    entry: SmartThingsConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Add climate entities for a config entry."""
    entry_data = entry.runtime_data
    entities: list[ClimateEntity] = [
        SmartThingsAirConditioner(entry_data.client, device)
        for device in entry_data.devices.values()
        if all(capability in device.status[MAIN] for capability in AC_CAPABILITIES)
    ]
    entities.extend(
        SmartThingsThermostat(entry_data.client, device)
        for device in entry_data.devices.values()
        if all(
            capability in device.status[MAIN] for capability in THERMOSTAT_CAPABILITIES
        )
    )
    entities.extend(
        SmartThingsHeatPumpZone(entry_data.client, device, component)
        for device in entry_data.devices.values()
        for component in device.status
        if component in {"INDOOR", "INDOOR1", "INDOOR2"}
        and all(
            capability in device.status[component]
            for capability in HEAT_PUMP_CAPABILITIES
        )
    )
    async_add_entities(entities)