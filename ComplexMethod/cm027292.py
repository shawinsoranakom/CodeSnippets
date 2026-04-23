async def async_setup_entry(
    hass: HomeAssistant,
    entry: TessieConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the Tessie binary sensor platform from a config entry."""
    async_add_entities(
        chain(
            (
                TessieBinarySensorEntity(vehicle, description)
                for vehicle in entry.runtime_data.vehicles
                for description in VEHICLE_DESCRIPTIONS
            ),
            (
                TessieEnergyLiveBinarySensorEntity(energy, description)
                for energy in entry.runtime_data.energysites
                for description in ENERGY_LIVE_DESCRIPTIONS
                if energy.live_coordinator is not None
            ),
            (
                TessieEnergyInfoBinarySensorEntity(vehicle, description)
                for vehicle in entry.runtime_data.energysites
                for description in ENERGY_INFO_DESCRIPTIONS
            ),
        )
    )