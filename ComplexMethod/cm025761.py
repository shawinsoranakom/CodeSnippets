async def async_setup_entry(
    hass: HomeAssistant,
    entry: TeslaFleetConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the TeslaFleet select platform from a config entry."""

    async_add_entities(
        chain(
            (
                TeslaFleetSeatHeaterSelectEntity(
                    vehicle, description, entry.runtime_data.scopes
                )
                for description in SEAT_HEATER_DESCRIPTIONS
                for vehicle in entry.runtime_data.vehicles
            ),
            (
                TeslaFleetWheelHeaterSelectEntity(vehicle, entry.runtime_data.scopes)
                for vehicle in entry.runtime_data.vehicles
            ),
            (
                TeslaFleetOperationSelectEntity(energysite, entry.runtime_data.scopes)
                for energysite in entry.runtime_data.energysites
                if energysite.info_coordinator.data.get("components_battery")
            ),
            (
                TeslaFleetExportRuleSelectEntity(energysite, entry.runtime_data.scopes)
                for energysite in entry.runtime_data.energysites
                if energysite.info_coordinator.data.get("components_battery")
                and energysite.info_coordinator.data.get("components_solar")
            ),
        )
    )