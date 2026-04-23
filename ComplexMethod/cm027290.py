async def async_setup_entry(
    hass: HomeAssistant,
    entry: TessieConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the Tessie select platform from a config entry."""

    async_add_entities(
        chain(
            (
                TessieSeatHeaterSelectEntity(vehicle, key)
                for vehicle in entry.runtime_data.vehicles
                for key in SEAT_HEATERS
                if key
                in vehicle.data_coordinator.data  # not all vehicles have rear center or third row
            ),
            (
                TessieSeatCoolerSelectEntity(vehicle, key)
                for vehicle in entry.runtime_data.vehicles
                for key in SEAT_COOLERS
                if key
                in vehicle.data_coordinator.data  # not all vehicles have ventilated seats
            ),
            (
                TessieOperationSelectEntity(energysite)
                for energysite in entry.runtime_data.energysites
                if energysite.info_coordinator.data.get("components_battery")
            ),
            (
                TessieExportRuleSelectEntity(energysite)
                for energysite in entry.runtime_data.energysites
                if energysite.info_coordinator.data.get("components_battery")
                and energysite.info_coordinator.data.get("components_solar")
            ),
        )
    )