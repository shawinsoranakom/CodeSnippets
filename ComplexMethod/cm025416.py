async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: NexiaConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up sensors for a Nexia device."""

    coordinator = config_entry.runtime_data
    nexia_home = coordinator.nexia_home
    entities: list[NexiaThermostatEntity] = []

    # Thermostat / System Sensors
    for thermostat_id in nexia_home.get_thermostat_ids():
        thermostat: NexiaThermostat = nexia_home.get_thermostat_by_id(thermostat_id)

        entities.append(
            NexiaThermostatSensor(
                coordinator,
                thermostat,
                "get_system_status",
                "system_status",
                None,
                None,
                None,
            )
        )
        # Air cleaner
        entities.append(
            NexiaThermostatSensor(
                coordinator,
                thermostat,
                "get_air_cleaner_mode",
                "air_cleaner_mode",
                None,
                None,
                None,
            )
        )
        # Compressor Speed
        if thermostat.has_variable_speed_compressor():
            entities.append(
                NexiaThermostatSensor(
                    coordinator,
                    thermostat,
                    "get_current_compressor_speed",
                    "current_compressor_speed",
                    None,
                    PERCENTAGE,
                    SensorStateClass.MEASUREMENT,
                    percent_conv,
                )
            )
            entities.append(
                NexiaThermostatSensor(
                    coordinator,
                    thermostat,
                    "get_requested_compressor_speed",
                    "requested_compressor_speed",
                    None,
                    PERCENTAGE,
                    SensorStateClass.MEASUREMENT,
                    percent_conv,
                )
            )
        # Outdoor Temperature
        if thermostat.has_outdoor_temperature():
            if thermostat.get_unit() == UNIT_CELSIUS:
                unit = UnitOfTemperature.CELSIUS
            else:
                unit = UnitOfTemperature.FAHRENHEIT
            entities.append(
                NexiaThermostatSensor(
                    coordinator,
                    thermostat,
                    "get_outdoor_temperature",
                    "outdoor_temperature",
                    SensorDeviceClass.TEMPERATURE,
                    unit,
                    SensorStateClass.MEASUREMENT,
                )
            )
        # Relative Humidity
        if thermostat.has_relative_humidity():
            entities.append(
                NexiaThermostatSensor(
                    coordinator,
                    thermostat,
                    "get_relative_humidity",
                    None,
                    SensorDeviceClass.HUMIDITY,
                    PERCENTAGE,
                    SensorStateClass.MEASUREMENT,
                    percent_conv,
                )
            )
        # Heating Humidification Setpoint
        if thermostat.has_humidify_support():
            entities.append(
                NexiaThermostatSensor(
                    coordinator,
                    thermostat,
                    "get_humidify_setpoint",
                    "get_humidify_setpoint",
                    SensorDeviceClass.HUMIDITY,
                    PERCENTAGE,
                    SensorStateClass.MEASUREMENT,
                    percent_conv,
                )
            )

        # Cooling Dehumidification Setpoint
        if thermostat.has_dehumidify_support():
            entities.append(
                NexiaThermostatSensor(
                    coordinator,
                    thermostat,
                    "get_dehumidify_setpoint",
                    "get_dehumidify_setpoint",
                    SensorDeviceClass.HUMIDITY,
                    PERCENTAGE,
                    SensorStateClass.MEASUREMENT,
                    percent_conv,
                )
            )

        # Zone Sensors
        for zone_id in thermostat.get_zone_ids():
            zone = thermostat.get_zone_by_id(zone_id)
            if thermostat.get_unit() == UNIT_CELSIUS:
                unit = UnitOfTemperature.CELSIUS
            else:
                unit = UnitOfTemperature.FAHRENHEIT
            # Temperature
            entities.append(
                NexiaThermostatZoneSensor(
                    coordinator,
                    zone,
                    "get_temperature",
                    None,
                    SensorDeviceClass.TEMPERATURE,
                    unit,
                    SensorStateClass.MEASUREMENT,
                    None,
                )
            )
            # Zone Status
            entities.append(
                NexiaThermostatZoneSensor(
                    coordinator, zone, "get_status", "zone_status", None, None, None
                )
            )
            # Setpoint Status
            entities.append(
                NexiaThermostatZoneSensor(
                    coordinator,
                    zone,
                    "get_setpoint_status",
                    "zone_setpoint_status",
                    None,
                    None,
                    None,
                )
            )

    async_add_entities(entities)