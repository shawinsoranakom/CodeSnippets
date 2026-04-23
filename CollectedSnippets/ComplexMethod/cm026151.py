async def async_setup_entry(
    hass: HomeAssistant,
    entry: PowerfoxConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Powerfox sensors based on a config entry."""
    entities: list[SensorEntity] = []
    for coordinator in entry.runtime_data:
        if isinstance(coordinator, PowerfoxReportDataUpdateCoordinator):
            gas_report = coordinator.data.gas
            if gas_report is None:
                continue
            entities.extend(
                PowerfoxGasSensorEntity(
                    coordinator=coordinator,
                    description=description,
                    device=coordinator.device,
                )
                for description in SENSORS_GAS
                if description.value_fn(gas_report) is not None
            )
            continue
        if isinstance(coordinator.data, PowerMeter):
            entities.extend(
                PowerfoxSensorEntity(
                    coordinator=coordinator,
                    description=description,
                    device=coordinator.device,
                )
                for description in SENSORS_POWER
                if description.value_fn(coordinator.data) is not None
            )
        if isinstance(coordinator.data, WaterMeter):
            entities.extend(
                PowerfoxSensorEntity(
                    coordinator=coordinator,
                    description=description,
                    device=coordinator.device,
                )
                for description in SENSORS_WATER
            )
        if isinstance(coordinator.data, HeatMeter):
            entities.extend(
                PowerfoxSensorEntity(
                    coordinator=coordinator,
                    description=description,
                    device=coordinator.device,
                )
                for description in SENSORS_HEAT
            )
    async_add_entities(entities)