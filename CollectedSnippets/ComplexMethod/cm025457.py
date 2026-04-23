async def async_setup_entry(
    hass: HomeAssistant,
    entry: TeslemetryConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the Teslemetry binary sensor platform from a config entry."""

    entities: list[BinarySensorEntity] = []
    for vehicle in entry.runtime_data.vehicles:
        for description in VEHICLE_DESCRIPTIONS:
            if (
                not vehicle.poll
                and description.streaming_listener
                and vehicle.firmware >= description.streaming_firmware
            ):
                entities.append(
                    TeslemetryVehicleStreamingBinarySensorEntity(vehicle, description)
                )
            elif description.polling:
                entities.append(
                    TeslemetryVehiclePollingBinarySensorEntity(vehicle, description)
                )

    entities.extend(
        TeslemetryEnergyLiveBinarySensorEntity(energysite, description)
        for energysite in entry.runtime_data.energysites
        if energysite.live_coordinator
        for description in ENERGY_LIVE_DESCRIPTIONS
        if description.key in energysite.live_coordinator.data
    )
    entities.extend(
        TeslemetryEnergyInfoBinarySensorEntity(energysite, description)
        for energysite in entry.runtime_data.energysites
        for description in ENERGY_INFO_DESCRIPTIONS
        if description.key in energysite.info_coordinator.data
    )

    async_add_entities(entities)