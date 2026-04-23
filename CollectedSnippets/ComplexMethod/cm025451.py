async def async_setup_entry(
    hass: HomeAssistant,
    entry: TeslemetryConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the Teslemetry select platform from a config entry."""

    async_add_entities(
        chain(
            (
                TeslemetryVehiclePollingSelectEntity(
                    vehicle, description, entry.runtime_data.scopes
                )
                if vehicle.poll
                or vehicle.firmware < "2024.26"
                or description.streaming_listener is None
                else TeslemetryStreamingSelectEntity(
                    vehicle, description, entry.runtime_data.scopes
                )
                for description in VEHICLE_DESCRIPTIONS
                for vehicle in entry.runtime_data.vehicles
                if description.supported_fn(vehicle.coordinator.data)
            ),
            (
                TeslemetryOperationSelectEntity(energysite, entry.runtime_data.scopes)
                for energysite in entry.runtime_data.energysites
                if energysite.info_coordinator.data.get("components_battery")
            ),
            (
                TeslemetryExportRuleSelectEntity(energysite, entry.runtime_data.scopes)
                for energysite in entry.runtime_data.energysites
                if energysite.info_coordinator.data.get("components_battery")
                and energysite.info_coordinator.data.get("components_solar")
            ),
        )
    )