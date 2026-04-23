async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ReolinkConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up a Reolink IP Camera."""
    reolink_data: ReolinkData = config_entry.runtime_data
    api = reolink_data.host.api

    entities: list[BinarySensorEntity] = []
    for channel in api.channels:
        entities.extend(
            ReolinkPushBinarySensorEntity(reolink_data, channel, entity_description)
            for entity_description in BINARY_PUSH_SENSORS
            if entity_description.supported(api, channel)
        )
        entities.extend(
            ReolinkBinarySensorEntity(reolink_data, channel, entity_description)
            for entity_description in BINARY_SENSORS
            if entity_description.supported(api, channel)
        )
        entities.extend(
            ReolinkSmartAIBinarySensorEntity(
                reolink_data, channel, location, entity_description
            )
            for entity_description in BINARY_SMART_AI_SENSORS
            for location in api.baichuan.smart_location_list(
                channel, entity_description.smart_type
            )
            if entity_description.supported(api, channel, location)
        )
        entities.extend(
            ReolinkIndexBinarySensorEntity(
                reolink_data, channel, index, BINARY_IO_INPUT_SENSOR
            )
            for index in api.baichuan.io_inputs(channel)
        )

    async_add_entities(entities)