async def async_setup_entry(
    hass: HomeAssistant,
    entry: TessieConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the Tessie sensor platform from a config entry."""

    async_add_entities(
        chain(
            (  # Add vehicles
                TessieVehicleSensorEntity(vehicle, description)
                for vehicle in entry.runtime_data.vehicles
                for description in DESCRIPTIONS
            ),
            (  # Add energy site info
                TessieEnergyInfoSensorEntity(energysite, description)
                for energysite in entry.runtime_data.energysites
                for description in ENERGY_INFO_DESCRIPTIONS
                if description.key in energysite.info_coordinator.data
            ),
            (  # Add energy site live
                TessieEnergyLiveSensorEntity(energysite, description)
                for energysite in entry.runtime_data.energysites
                for description in ENERGY_LIVE_DESCRIPTIONS
                if energysite.live_coordinator is not None
                and (
                    description.key in energysite.live_coordinator.data
                    or description.key == "percentage_charged"
                )
            ),
            (  # Add wall connectors
                TessieWallConnectorSensorEntity(energysite, din, description)
                for energysite in entry.runtime_data.energysites
                if energysite.live_coordinator is not None
                for din in energysite.live_coordinator.data.get("wall_connectors", {})
                for description in WALL_CONNECTOR_DESCRIPTIONS
            ),
            (  # Add energy history
                TessieEnergyHistorySensorEntity(energysite, description)
                for energysite in entry.runtime_data.energysites
                for description in ENERGY_HISTORY_DESCRIPTIONS
                if energysite.history_coordinator is not None
            ),
        )
    )