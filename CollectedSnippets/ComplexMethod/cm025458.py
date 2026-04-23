async def async_setup_entry(
    hass: HomeAssistant,
    entry: TeslemetryConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the Teslemetry Switch platform from a config entry."""

    entities: list[SwitchEntity] = []

    for vehicle in entry.runtime_data.vehicles:
        for description in VEHICLE_DESCRIPTIONS:
            if vehicle.poll or vehicle.firmware < description.streaming_firmware:
                if description.polling:
                    entities.append(
                        TeslemetryVehiclePollingVehicleSwitchEntity(
                            vehicle, description, entry.runtime_data.scopes
                        )
                    )
            else:
                entities.append(
                    TeslemetryStreamingVehicleSwitchEntity(
                        vehicle, description, entry.runtime_data.scopes
                    )
                )

    entities.extend(
        TeslemetryChargeFromGridSwitchEntity(
            energysite,
            entry.runtime_data.scopes,
        )
        for energysite in entry.runtime_data.energysites
        if energysite.info_coordinator.data.get("components_battery")
        and energysite.info_coordinator.data.get("components_solar")
    )
    entities.extend(
        TeslemetryStormModeSwitchEntity(energysite, entry.runtime_data.scopes)
        for energysite in entry.runtime_data.energysites
        if energysite.info_coordinator.data.get("components_storm_mode_capable")
    )

    async_add_entities(entities)