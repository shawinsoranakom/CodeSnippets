async def async_setup_entry(
    hass: HomeAssistant,
    entry: TeslaFleetConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the Tesla Fleet binary sensor platform from a config entry."""

    async_add_entities(
        chain(
            (  # Vehicles
                TeslaFleetVehicleBinarySensorEntity(vehicle, description)
                for vehicle in entry.runtime_data.vehicles
                for description in VEHICLE_DESCRIPTIONS
            ),
            (  # Energy Site Live
                TeslaFleetEnergyLiveBinarySensorEntity(energysite, description)
                for energysite in entry.runtime_data.energysites
                for description in ENERGY_LIVE_DESCRIPTIONS
                if energysite.info_coordinator.data.get("components_battery")
            ),
            (  # Energy Site Info
                TeslaFleetEnergyInfoBinarySensorEntity(energysite, description)
                for energysite in entry.runtime_data.energysites
                for description in ENERGY_INFO_DESCRIPTIONS
                if energysite.info_coordinator.data.get("components_battery")
            ),
        )
    )