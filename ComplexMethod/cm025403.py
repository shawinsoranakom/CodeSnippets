async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: RoborockConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the Roborock vacuum binary sensors."""
    entities: list[BinarySensorEntity] = [
        RoborockBinarySensorEntity(
            coordinator,
            description,
        )
        for coordinator in config_entry.runtime_data.v1
        for description in BINARY_SENSOR_DESCRIPTIONS
        # Note: Currently coordinator.data is always available on startup but won't be in the future
        if (
            coordinator.data is not None
            and description.value_fn(coordinator.data) is not None
        )
    ]
    entities.extend(
        RoborockBinarySensorEntityA01(
            coordinator,
            description,
        )
        for coordinator in config_entry.runtime_data.a01
        if isinstance(coordinator, RoborockWashingMachineUpdateCoordinator)
        for description in ZEO_BINARY_SENSOR_DESCRIPTIONS
        if description.data_protocol in coordinator.request_protocols
    )
    async_add_entities(entities)