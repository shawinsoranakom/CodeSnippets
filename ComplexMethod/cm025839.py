async def async_setup_entry(
    hass: HomeAssistant,
    entry: ThinqConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up an entry for sensor platform."""
    entities: list[ThinQSensorEntity | ThinQEnergySensorEntity] = []
    for coordinator in entry.runtime_data.coordinators.values():
        if (
            descriptions := DEVICE_TYPE_SENSOR_MAP.get(
                coordinator.api.device.device_type
            )
        ) is not None:
            for description in descriptions:
                entities.extend(
                    ThinQSensorEntity(coordinator, description, property_id)
                    for property_id in coordinator.api.get_active_idx(
                        description.key,
                        (
                            ActiveMode.READABLE
                            if (
                                coordinator.api.device.device_type == DeviceType.COOKTOP
                                or isinstance(description.key, TimerProperty)
                            )
                            else ActiveMode.READ_ONLY
                        ),
                    )
                )
        for energy_description in ENERGY_USAGE_SENSORS:
            entities.extend(
                ThinQEnergySensorEntity(
                    coordinator=coordinator,
                    entity_description=energy_description,
                    property_id=energy_property_id,
                    postfix_id=energy_description.key,
                )
                for energy_property_id in coordinator.api.get_active_idx(
                    (
                        ThinQPropertyEx.ENERGY_USAGE
                        if coordinator.sub_id is None
                        else f"{ThinQPropertyEx.ENERGY_USAGE}_{coordinator.sub_id}"
                    ),
                    ActiveMode.READ_ONLY,
                )
            )
    if entities:
        async_add_entities(entities)