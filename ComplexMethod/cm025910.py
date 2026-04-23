async def async_setup_entry(
    hass: HomeAssistant,
    entry: SFRConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the sensors."""
    data = entry.runtime_data
    system_info = data.system.data

    entities: list[SFRBoxBinarySensor] = [
        SFRBoxBinarySensor(data.wan, description, system_info)
        for description in WAN_SENSOR_TYPES
    ]
    if data.voip is not None:
        entities.extend(
            SFRBoxBinarySensor(data.voip, description, system_info)
            for description in VOIP_SENSOR_TYPES
        )
    if (net_infra := system_info.net_infra) == "adsl":
        entities.extend(
            SFRBoxBinarySensor(data.dsl, description, system_info)
            for description in DSL_SENSOR_TYPES
        )
    elif net_infra == "ftth":
        entities.extend(
            SFRBoxBinarySensor(data.ftth, description, system_info)
            for description in FTTH_SENSOR_TYPES
        )

    async_add_entities(entities)