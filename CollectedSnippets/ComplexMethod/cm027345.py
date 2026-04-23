async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: BoschConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the SHC sensor platform."""
    session = config_entry.runtime_data

    entities: list[SensorEntity] = [
        SHCSensor(
            device,
            SENSOR_DESCRIPTIONS[sensor_type],
            session.information.unique_id,
            config_entry.entry_id,
        )
        for device in session.device_helper.thermostats
        for sensor_type in (TEMPERATURE_SENSOR, VALVE_TAPPET_SENSOR)
    ]

    entities.extend(
        SHCSensor(
            device,
            SENSOR_DESCRIPTIONS[sensor_type],
            session.information.unique_id,
            config_entry.entry_id,
        )
        for device in session.device_helper.wallthermostats
        for sensor_type in (TEMPERATURE_SENSOR, HUMIDITY_SENSOR)
    )

    entities.extend(
        SHCSensor(
            device,
            SENSOR_DESCRIPTIONS[sensor_type],
            session.information.unique_id,
            config_entry.entry_id,
        )
        for device in session.device_helper.twinguards
        for sensor_type in (
            TEMPERATURE_SENSOR,
            HUMIDITY_SENSOR,
            PURITY_SENSOR,
            AIR_QUALITY_SENSOR,
            TEMPERATURE_RATING_SENSOR,
            HUMIDITY_RATING_SENSOR,
            PURITY_RATING_SENSOR,
        )
    )

    entities.extend(
        SHCSensor(
            device,
            SENSOR_DESCRIPTIONS[sensor_type],
            session.information.unique_id,
            config_entry.entry_id,
        )
        for device in (
            session.device_helper.smart_plugs + session.device_helper.light_switches_bsm
        )
        for sensor_type in (POWER_SENSOR, ENERGY_SENSOR)
    )

    entities.extend(
        SHCSensor(
            device,
            SENSOR_DESCRIPTIONS[sensor_type],
            session.information.unique_id,
            config_entry.entry_id,
        )
        for device in session.device_helper.smart_plugs_compact
        for sensor_type in (POWER_SENSOR, ENERGY_SENSOR, COMMUNICATION_QUALITY_SENSOR)
    )

    async_add_entities(entities)