async def async_setup_entry(
    hass: HomeAssistant,
    entry: SmartThingsConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Add fans for a config entry."""
    entry_data = entry.runtime_data
    entities: list[FanEntity] = [
        SmartThingsFan(entry_data.client, device)
        for device in entry_data.devices.values()
        if Capability.SWITCH in device.status[MAIN]
        and any(
            capability in device.status[MAIN]
            for capability in (
                Capability.FAN_SPEED,
                Capability.AIR_CONDITIONER_FAN_MODE,
            )
        )
        and Capability.THERMOSTAT_COOLING_SETPOINT not in device.status[MAIN]
    ]
    entities.extend(
        SmartThingsHood(entry_data.client, device)
        for device in entry_data.devices.values()
        if Capability.SWITCH in device.status[MAIN]
        and Capability.SAMSUNG_CE_HOOD_FAN_SPEED in device.status[MAIN]
        and (
            device.status[MAIN][Capability.SAMSUNG_CE_HOOD_FAN_SPEED][
                Attribute.SETTABLE_MIN_FAN_SPEED
            ].value
            == SMART
        )
    )
    async_add_entities(entities)