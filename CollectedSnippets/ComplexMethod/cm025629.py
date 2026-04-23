async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: EnphaseConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up envoy binary sensor platform."""
    coordinator = config_entry.runtime_data
    envoy_data = coordinator.envoy.data
    assert envoy_data is not None
    entities: list[BinarySensorEntity] = []
    if envoy_data.encharge_inventory:
        entities.extend(
            EnvoyEnchargeBinarySensorEntity(coordinator, description, encharge)
            for description in ENCHARGE_SENSORS
            for encharge in envoy_data.encharge_inventory
        )

    if envoy_data.enpower:
        entities.extend(
            EnvoyEnpowerBinarySensorEntity(coordinator, description)
            for description in ENPOWER_SENSORS
        )

    if envoy_data.collar:
        entities.extend(
            EnvoyCollarBinarySensorEntity(coordinator, description)
            for description in COLLAR_SENSORS
        )

    if envoy_data.c6cc:
        entities.extend(
            EnvoyC6CCBinarySensorEntity(coordinator, description)
            for description in C6CC_SENSORS
        )

    async_add_entities(entities)