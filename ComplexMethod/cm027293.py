async def async_setup_entry(
    hass: HomeAssistant,
    entry: TessieConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the Tessie Switch platform from a config entry."""

    async_add_entities(
        chain(
            (
                TessieSwitchEntity(vehicle, description)
                for vehicle in entry.runtime_data.vehicles
                for description in DESCRIPTIONS
                if description.key in vehicle.data_coordinator.data
            ),
            (
                TessieChargeFromGridSwitchEntity(energysite)
                for energysite in entry.runtime_data.energysites
                if energysite.info_coordinator.data.get("components_battery")
                and energysite.info_coordinator.data.get("components_solar")
            ),
            (
                TessieStormModeSwitchEntity(energysite)
                for energysite in entry.runtime_data.energysites
                if energysite.info_coordinator.data.get("components_storm_mode_capable")
            ),
        )
    )