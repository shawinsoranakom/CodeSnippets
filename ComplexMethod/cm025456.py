async def async_setup_entry(
    hass: HomeAssistant,
    entry: TeslemetryConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the Teslemetry number platform from a config entry."""

    async_add_entities(
        chain(
            (
                TeslemetryVehiclePollingNumberEntity(
                    vehicle,
                    description,
                    entry.runtime_data.scopes,
                )
                if vehicle.poll or vehicle.firmware < "2024.26"
                else TeslemetryStreamingNumberEntity(
                    vehicle,
                    description,
                    entry.runtime_data.scopes,
                )
                for vehicle in entry.runtime_data.vehicles
                for description in VEHICLE_DESCRIPTIONS
            ),
            (
                TeslemetryEnergyInfoNumberSensorEntity(
                    energysite,
                    description,
                    entry.runtime_data.scopes,
                )
                for energysite in entry.runtime_data.energysites
                for description in ENERGY_INFO_DESCRIPTIONS
                if description.requires is None
                or energysite.info_coordinator.data.get(description.requires)
            ),
        )
    )