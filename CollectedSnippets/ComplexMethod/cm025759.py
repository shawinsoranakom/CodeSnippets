async def async_setup_entry(
    hass: HomeAssistant,
    entry: TeslaFleetConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the Tesla Fleet sensor platform from a config entry."""
    async_add_entities(
        chain(
            (  # Add vehicles
                TeslaFleetVehicleSensorEntity(vehicle, description)
                for vehicle in entry.runtime_data.vehicles
                for description in VEHICLE_DESCRIPTIONS
            ),
            (  # Add vehicles time sensors
                TeslaFleetVehicleTimeSensorEntity(vehicle, description)
                for vehicle in entry.runtime_data.vehicles
                for description in VEHICLE_TIME_DESCRIPTIONS
            ),
            (  # Add energy site live
                TeslaFleetEnergyLiveSensorEntity(energysite, description)
                for energysite in entry.runtime_data.energysites
                for description in ENERGY_LIVE_DESCRIPTIONS
                if description.key in energysite.live_coordinator.data
                or description.key == "percentage_charged"
            ),
            (  # Add energy site history
                TeslaFleetEnergyHistorySensorEntity(energysite, description)
                for energysite in entry.runtime_data.energysites
                for description in ENERGY_HISTORY_DESCRIPTIONS
                if energysite.info_coordinator.data.get("components_battery")
                or energysite.info_coordinator.data.get("components_solar")
            ),
            (  # Add wall connectors
                TeslaFleetWallConnectorSensorEntity(energysite, wc["din"], description)
                for energysite in entry.runtime_data.energysites
                for wc in energysite.info_coordinator.data.get(
                    "components_wall_connectors", []
                )
                if "din" in wc
                for description in WALL_CONNECTOR_DESCRIPTIONS
            ),
            (  # Add energy site info
                TeslaFleetEnergyInfoSensorEntity(energysite, description)
                for energysite in entry.runtime_data.energysites
                for description in ENERGY_INFO_DESCRIPTIONS
                if description.key in energysite.info_coordinator.data
            ),
        )
    )