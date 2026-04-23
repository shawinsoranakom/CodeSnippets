async def add_switch_entities(
    config_entry: HomeeConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
    nodes: list[HomeeNode],
) -> None:
    """Add homee switch entities."""
    async_add_entities(
        HomeeSwitch(attribute, config_entry, SWITCH_DESCRIPTIONS[attribute.type])
        for node in nodes
        for attribute in node.attributes
        if (attribute.type in SWITCH_DESCRIPTIONS and attribute.editable)
        and not (
            attribute.type == AttributeType.ON_OFF and node.profile in LIGHT_PROFILES
        )
        and not (
            attribute.type == AttributeType.MANUAL_OPERATION
            and node.profile in CLIMATE_PROFILES
        )
    )