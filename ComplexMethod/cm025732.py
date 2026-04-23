async def async_setup_entry(
    hass: HomeAssistant,
    entry: WeheatConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the sensors for weheat heat pump."""

    entities: list[WeheatHeatPumpSensor] = []
    for weheatdata in entry.runtime_data:
        entities.extend(
            WeheatHeatPumpSensor(
                weheatdata.heat_pump_info,
                weheatdata.data_coordinator,
                entity_description,
            )
            for entity_description in SENSORS
            if entity_description.value_fn(weheatdata.data_coordinator.data) is not None
        )
        if weheatdata.heat_pump_info.has_dhw:
            entities.extend(
                WeheatHeatPumpSensor(
                    weheatdata.heat_pump_info,
                    weheatdata.data_coordinator,
                    entity_description,
                )
                for entity_description in DHW_SENSORS
                if entity_description.value_fn(weheatdata.data_coordinator.data)
                is not None
            )
            entities.extend(
                WeheatHeatPumpSensor(
                    weheatdata.heat_pump_info,
                    weheatdata.energy_coordinator,
                    entity_description,
                )
                for entity_description in DHW_ENERGY_SENSORS
                if entity_description.value_fn(weheatdata.energy_coordinator.data)
                is not None
            )
        entities.extend(
            WeheatHeatPumpSensor(
                weheatdata.heat_pump_info,
                weheatdata.energy_coordinator,
                entity_description,
            )
            for entity_description in ENERGY_SENSORS
            if entity_description.value_fn(weheatdata.energy_coordinator.data)
            is not None
        )

    async_add_entities(entities)