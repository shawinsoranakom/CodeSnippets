async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: GrowattConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the Growatt sensor."""
    # Use runtime_data instead of hass.data
    data = config_entry.runtime_data

    entities: list[GrowattSensor] = []

    # Add total sensors
    total_coordinator = data.total_coordinator
    entities.extend(
        GrowattSensor(
            total_coordinator,
            name=f"{config_entry.data['name']} Total",
            serial_id=config_entry.data["plant_id"],
            unique_id=f"{config_entry.data['plant_id']}-{description.key}",
            description=description,
        )
        for description in TOTAL_SENSOR_TYPES
    )

    # Add sensors for each device
    for device_sn, device_coordinator in data.devices.items():
        sensor_descriptions: list = []
        if device_coordinator.device_type == "inverter":
            sensor_descriptions = list(INVERTER_SENSOR_TYPES)
        elif device_coordinator.device_type in ("tlx", "min"):
            sensor_descriptions = list(TLX_SENSOR_TYPES)
        elif device_coordinator.device_type == "storage":
            sensor_descriptions = list(STORAGE_SENSOR_TYPES)
        elif device_coordinator.device_type == "mix":
            sensor_descriptions = list(MIX_SENSOR_TYPES)
        elif device_coordinator.device_type == "sph":
            sensor_descriptions = list(SPH_SENSOR_TYPES)
        else:
            _LOGGER.debug(
                "Device type %s was found but is not supported right now",
                device_coordinator.device_type,
            )

        entities.extend(
            GrowattSensor(
                device_coordinator,
                name=device_sn,
                serial_id=device_sn,
                unique_id=f"{device_sn}-{description.key}",
                description=description,
            )
            for description in sensor_descriptions
        )

    async_add_entities(entities)