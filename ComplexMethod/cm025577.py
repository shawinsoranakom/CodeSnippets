async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ReolinkConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up a Reolink IP Camera."""
    reolink_data: ReolinkData = config_entry.runtime_data

    entities: list[
        ReolinkSensorEntity | ReolinkHostSensorEntity | ReolinkHddSensorEntity
    ] = [
        ReolinkSensorEntity(reolink_data, channel, entity_description)
        for entity_description in SENSORS
        for channel in reolink_data.host.api.channels
        if entity_description.supported(reolink_data.host.api, channel)
    ]
    entities.extend(
        ReolinkHostSensorEntity(reolink_data, entity_description)
        for entity_description in HOST_SENSORS
        if entity_description.supported(reolink_data.host.api)
    )
    entities.extend(
        ReolinkHddSensorEntity(reolink_data, hdd_index, entity_description)
        for entity_description in HDD_SENSORS
        for hdd_index in reolink_data.host.api.hdd_list
        if entity_description.supported(reolink_data.host.api, hdd_index)
    )
    async_add_entities(entities)