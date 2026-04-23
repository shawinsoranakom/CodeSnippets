async def async_setup_entry(
    hass: HomeAssistant,
    entry: IskraConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Iskra sensors based on config_entry."""

    # Device that uses the config entry.
    coordinators = entry.runtime_data

    entities: list[IskraSensor] = []

    # Add sensors for each device.
    for coordinator in coordinators:
        device = coordinator.device
        sensors = []

        # Add measurement sensors.
        if device.supports_measurements:
            sensors.append(ATTR_FREQUENCY)
            sensors.append(ATTR_TOTAL_APPARENT_POWER)
            sensors.append(ATTR_TOTAL_ACTIVE_POWER)
            sensors.append(ATTR_TOTAL_REACTIVE_POWER)
            if device.phases >= 1:
                sensors.append(ATTR_PHASE1_VOLTAGE)
                sensors.append(ATTR_PHASE1_POWER)
                sensors.append(ATTR_PHASE1_CURRENT)
            if device.phases >= 2:
                sensors.append(ATTR_PHASE2_VOLTAGE)
                sensors.append(ATTR_PHASE2_POWER)
                sensors.append(ATTR_PHASE2_CURRENT)
            if device.phases >= 3:
                sensors.append(ATTR_PHASE3_VOLTAGE)
                sensors.append(ATTR_PHASE3_POWER)
                sensors.append(ATTR_PHASE3_CURRENT)

        entities.extend(
            IskraSensor(coordinator, description)
            for description in SENSOR_TYPES
            if description.key in sensors
        )

        if device.supports_counters:
            for index, counter in enumerate(device.counters.non_resettable[:4]):
                description = get_counter_entity_description(
                    counter, index, ATTR_NON_RESETTABLE_COUNTER
                )
                entities.append(IskraSensor(coordinator, description))

            for index, counter in enumerate(device.counters.resettable[:8]):
                description = get_counter_entity_description(
                    counter, index, ATTR_RESETTABLE_COUNTER
                )
                entities.append(IskraSensor(coordinator, description))

    async_add_entities(entities)