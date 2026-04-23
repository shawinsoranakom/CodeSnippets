async def async_setup_entry(
    hass: HomeAssistant,
    entry: SolarlogConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Add solarlog entry."""

    solarLogIntegrationData: SolarlogIntegrationData = entry.runtime_data

    entities: list[SensorEntity] = [
        SolarLogBasicCoordinatorSensor(
            solarLogIntegrationData.basic_data_coordinator, sensor
        )
        for sensor in SOLARLOG_BASIC_SENSOR_TYPES
    ]

    if solarLogIntegrationData.longtime_data_coordinator is not None:
        entities.extend(
            SolarLogLongtimeCoordinatorSensor(
                solarLogIntegrationData.longtime_data_coordinator, sensor
            )
            for sensor in SOLARLOG_LONGTIME_SENSOR_TYPES
        )

        # add battery sensors only if respective data is available (otherwise no battery attached to solarlog)
        if solarLogIntegrationData.basic_data_coordinator.data.battery_data is not None:
            entities.extend(
                SolarLogBatterySensor(
                    solarLogIntegrationData.basic_data_coordinator, sensor
                )
                for sensor in SOLARLOG_BATTERY_SENSOR_TYPES
            )

        if solarLogIntegrationData.device_data_coordinator is not None:
            device_data = solarLogIntegrationData.device_data_coordinator.data

            if device_data:
                entities.extend(
                    SolarLogInverterSensor(
                        solarLogIntegrationData.device_data_coordinator,
                        sensor,
                        device_id,
                    )
                    for device_id in device_data
                    for sensor in SOLARLOG_INVERTER_SENSOR_TYPES
                )

            def _async_add_new_device(device_id: int) -> None:
                async_add_entities(
                    SolarLogInverterSensor(
                        solarLogIntegrationData.device_data_coordinator,
                        sensor,
                        device_id,
                    )
                    for sensor in SOLARLOG_INVERTER_SENSOR_TYPES
                    if solarLogIntegrationData.device_data_coordinator is not None
                )

            solarLogIntegrationData.device_data_coordinator.new_device_callbacks.append(
                _async_add_new_device
            )

    async_add_entities(entities)