async def async_setup_entry(
    hass: HomeAssistant,
    entry: TeslemetryConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the Teslemetry cover platform from a config entry."""

    async_add_entities(
        chain(
            (
                TeslemetryVehiclePollingWindowEntity(vehicle, entry.runtime_data.scopes)
                if vehicle.poll or vehicle.firmware < "2024.26"
                else TeslemetryStreamingWindowEntity(vehicle, entry.runtime_data.scopes)
                for vehicle in entry.runtime_data.vehicles
            ),
            (
                TeslemetryVehiclePollingChargePortEntity(
                    vehicle, entry.runtime_data.scopes
                )
                if vehicle.poll or vehicle.firmware < "2024.44.25"
                else TeslemetryStreamingChargePortEntity(
                    vehicle, entry.runtime_data.scopes
                )
                for vehicle in entry.runtime_data.vehicles
            ),
            (
                TeslemetryVehiclePollingFrontTrunkEntity(
                    vehicle, entry.runtime_data.scopes
                )
                if vehicle.poll or vehicle.firmware < "2024.26"
                else TeslemetryStreamingFrontTrunkEntity(
                    vehicle, entry.runtime_data.scopes
                )
                for vehicle in entry.runtime_data.vehicles
            ),
            (
                TeslemetryVehiclePollingRearTrunkEntity(
                    vehicle, entry.runtime_data.scopes
                )
                if vehicle.poll or vehicle.firmware < "2024.26"
                else TeslemetryStreamingRearTrunkEntity(
                    vehicle, entry.runtime_data.scopes
                )
                for vehicle in entry.runtime_data.vehicles
            ),
            (
                TeslemetrySunroofEntity(vehicle, entry.runtime_data.scopes)
                for vehicle in entry.runtime_data.vehicles
                if vehicle.poll
                and vehicle.coordinator.data.get("vehicle_config_sun_roof_installed")
            ),
        )
    )