async def async_setup_entry(
    hass: HomeAssistant,
    entry: TeslemetryConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the Teslemetry sensor platform from a config entry."""

    entities: list[SensorEntity] = []
    for vehicle in entry.runtime_data.vehicles:
        for description in VEHICLE_DESCRIPTIONS:
            if (
                not vehicle.poll
                and description.streaming_listener
                and vehicle.firmware >= description.streaming_firmware
            ):
                entities.append(TeslemetryStreamSensorEntity(vehicle, description))
            elif description.polling:
                entities.append(TeslemetryVehicleSensorEntity(vehicle, description))

        for time_description in VEHICLE_TIME_DESCRIPTIONS:
            if (
                not vehicle.poll
                and vehicle.firmware >= time_description.streaming_firmware
            ):
                entities.append(
                    TeslemetryStreamTimeSensorEntity(vehicle, time_description)
                )
            else:
                entities.append(
                    TeslemetryVehicleTimeSensorEntity(vehicle, time_description)
                )

    entities.extend(
        TeslemetryEnergyLiveSensorEntity(energysite, description)
        for energysite in entry.runtime_data.energysites
        if energysite.live_coordinator
        for description in ENERGY_LIVE_DESCRIPTIONS
        if description.key in energysite.live_coordinator.data
        or description.key == "percentage_charged"
    )

    entities.extend(
        TeslemetryWallConnectorSensorEntity(energysite, din, description)
        for energysite in entry.runtime_data.energysites
        if energysite.live_coordinator
        for din in energysite.live_coordinator.data.get("wall_connectors", {})
        for description in WALL_CONNECTOR_DESCRIPTIONS
    )

    entities.extend(
        TeslemetryEnergyInfoSensorEntity(energysite, description)
        for energysite in entry.runtime_data.energysites
        for description in ENERGY_INFO_DESCRIPTIONS
        if description.key in energysite.info_coordinator.data
    )

    entities.extend(
        TeslemetryEnergyHistorySensorEntity(energysite, description)
        for energysite in entry.runtime_data.energysites
        for description in ENERGY_HISTORY_DESCRIPTIONS
        if energysite.history_coordinator is not None
    )

    if entry.runtime_data.stream is not None:
        entities.append(
            TeslemetryCreditBalanceSensor(
                entry.unique_id or entry.entry_id, entry.runtime_data.stream
            )
        )

    async_add_entities(entities)