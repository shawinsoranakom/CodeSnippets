async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: RoborockConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the Roborock vacuum sensors."""
    coordinators = config_entry.runtime_data

    entities: list[RoborockEntity] = [
        RoborockSensorEntity(
            coordinator,
            description,
        )
        for coordinator in coordinators.v1
        for description in SENSOR_DESCRIPTIONS
        # Note: Currently coordinator.data is always available on startup but won't be in the future
        if (
            coordinator.data is not None
            and description.value_fn(coordinator.data) is not None
        )
    ]
    entities.extend(RoborockCurrentRoom(coordinator) for coordinator in coordinators.v1)
    entities.extend(
        RoborockSensorEntityA01(
            coordinator,
            description,
        )
        for coordinator in coordinators.a01
        if isinstance(coordinator, RoborockWetDryVacUpdateCoordinator)
        for description in DYAD_SENSOR_DESCRIPTIONS
        if description.data_protocol in coordinator.request_protocols
    )
    entities.extend(
        RoborockSensorEntityA01(
            coordinator,
            description,
        )
        for coordinator in coordinators.a01
        if isinstance(coordinator, RoborockWashingMachineUpdateCoordinator)
        for description in ZEO_SENSOR_DESCRIPTIONS
        if description.data_protocol in coordinator.request_protocols
    )
    entities.extend(
        RoborockSensorEntityB01Q7(coordinator, description)
        for coordinator in coordinators.b01_q7
        for description in Q7_B01_SENSOR_DESCRIPTIONS
        if description.value_fn(coordinator.data) is not None
    )
    entities.extend(
        RoborockSensorEntityB01Q10(coordinator, description)
        for coordinator in coordinators.b01_q10
        for description in Q10_B01_SENSOR_DESCRIPTIONS
    )
    async_add_entities(entities)