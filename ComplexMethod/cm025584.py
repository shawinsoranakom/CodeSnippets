async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ReolinkConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up a Reolink number entities."""
    reolink_data: ReolinkData = config_entry.runtime_data
    api = reolink_data.host.api

    entities: list[NumberEntity] = [
        ReolinkNumberEntity(reolink_data, channel, entity_description)
        for entity_description in NUMBER_ENTITIES
        for channel in api.channels
        if entity_description.supported(api, channel)
    ]
    entities.extend(
        ReolinkSmartAINumberEntity(reolink_data, channel, location, entity_description)
        for entity_description in SMART_AI_NUMBER_ENTITIES
        for channel in api.channels
        for location in api.baichuan.smart_location_list(
            channel, entity_description.smart_type
        )
        if entity_description.supported(api, channel)
    )
    entities.extend(
        ReolinkHostNumberEntity(reolink_data, entity_description)
        for entity_description in HOST_NUMBER_ENTITIES
        if entity_description.supported(api)
    )
    entities.extend(
        ReolinkChimeNumberEntity(reolink_data, chime, entity_description)
        for entity_description in CHIME_NUMBER_ENTITIES
        for chime in api.chime_list
        if chime.channel is not None
    )
    entities.extend(
        ReolinkHostChimeNumberEntity(reolink_data, chime, entity_description)
        for entity_description in CHIME_NUMBER_ENTITIES
        for chime in api.chime_list
        if chime.channel is None
    )
    async_add_entities(entities)