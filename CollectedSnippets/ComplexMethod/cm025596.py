async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ReolinkConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up a Reolink switch entities."""
    reolink_data: ReolinkData = config_entry.runtime_data

    entities: list[SwitchEntity] = [
        ReolinkSwitchEntity(reolink_data, channel, entity_description)
        for entity_description in SWITCH_ENTITIES
        for channel in reolink_data.host.api.channels
        if entity_description.supported(reolink_data.host.api, channel)
    ]
    entities.extend(
        ReolinkHostSwitchEntity(reolink_data, entity_description)
        for entity_description in HOST_SWITCH_ENTITIES
        if entity_description.supported(reolink_data.host.api)
    )
    entities.extend(
        ReolinkChimeSwitchEntity(reolink_data, chime, entity_description)
        for entity_description in CHIME_SWITCH_ENTITIES
        for chime in reolink_data.host.api.chime_list
        if chime.channel is not None
    )
    entities.extend(
        ReolinkHostChimeSwitchEntity(reolink_data, chime, entity_description)
        for entity_description in CHIME_SWITCH_ENTITIES
        for chime in reolink_data.host.api.chime_list
        if chime.channel is None
    )
    entities.extend(
        ReolinkIndexSwitchEntity(reolink_data, channel, rule_id, RULE_SWITCH_ENTITY)
        for channel in reolink_data.host.api.channels
        for rule_id in reolink_data.host.api.baichuan.rule_ids(channel)
    )

    async_add_entities(entities)