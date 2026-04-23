async def async_setup_entry(
    hass: HomeAssistant,
    entry: OVOEnergyConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up OVO Energy sensor based on a config entry."""
    coordinator = entry.runtime_data

    entities = []

    if coordinator.data:
        if coordinator.data.electricity:
            for description in SENSOR_TYPES_ELECTRICITY:
                if (
                    description.key == KEY_LAST_ELECTRICITY_COST
                    and coordinator.data.electricity[-1] is not None
                    and coordinator.data.electricity[-1].cost is not None
                ):
                    description = dataclasses.replace(
                        description,
                        native_unit_of_measurement=(
                            coordinator.data.electricity[-1].cost.currency_unit
                        ),
                    )
                entities.append(OVOEnergySensor(coordinator, description))
        if coordinator.data.gas:
            for description in SENSOR_TYPES_GAS:
                if (
                    description.key == KEY_LAST_GAS_COST
                    and coordinator.data.gas[-1] is not None
                    and coordinator.data.gas[-1].cost is not None
                ):
                    description = dataclasses.replace(
                        description,
                        native_unit_of_measurement=coordinator.data.gas[
                            -1
                        ].cost.currency_unit,
                    )
                entities.append(OVOEnergySensor(coordinator, description))

    async_add_entities(entities, True)