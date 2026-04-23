async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: SmappeeConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the Smappee sensor."""
    smappee_base = config_entry.runtime_data

    entities = []
    for service_location in smappee_base.smappee.service_locations.values():
        # Add all basic sensors (realtime values and aggregators)
        # Some are available in local only env
        entities.extend(
            [
                SmappeeSensor(
                    smappee_base=smappee_base,
                    service_location=service_location,
                    description=description,
                )
                for description in TREND_SENSORS
                if not service_location.local_polling or description.local_polling
            ]
        )

        if service_location.has_reactive_value:
            entities.extend(
                [
                    SmappeeSensor(
                        smappee_base=smappee_base,
                        service_location=service_location,
                        description=description,
                    )
                    for description in REACTIVE_SENSORS
                ]
            )

        # Add solar sensors (some are available in local only env)
        if service_location.has_solar_production:
            entities.extend(
                [
                    SmappeeSensor(
                        smappee_base=smappee_base,
                        service_location=service_location,
                        description=description,
                    )
                    for description in SOLAR_SENSORS
                    if not service_location.local_polling or description.local_polling
                ]
            )

        # Add all CT measurements
        entities.extend(
            [
                SmappeeSensor(
                    smappee_base=smappee_base,
                    service_location=service_location,
                    description=SmappeeSensorEntityDescription(
                        key="load",
                        name=measurement.name,
                        native_unit_of_measurement=UnitOfPower.WATT,
                        sensor_id=measurement_id,
                        device_class=SensorDeviceClass.POWER,
                        state_class=SensorStateClass.MEASUREMENT,
                    ),
                )
                for measurement_id, measurement in service_location.measurements.items()
            ]
        )

        # Add phase- and line voltages if available
        if service_location.has_voltage_values:
            entities.extend(
                [
                    SmappeeSensor(
                        smappee_base=smappee_base,
                        service_location=service_location,
                        description=description,
                    )
                    for description in VOLTAGE_SENSORS
                    if (
                        service_location.phase_type in description.phase_types
                        and not (
                            description.key.startswith("line_")
                            and service_location.local_polling
                        )
                    )
                ]
            )

        # Add Gas and Water sensors
        entities.extend(
            [
                SmappeeSensor(
                    smappee_base=smappee_base,
                    service_location=service_location,
                    description=SmappeeSensorEntityDescription(
                        key="sensor",
                        name=channel.get("name"),
                        icon=(
                            "mdi:water"
                            if channel.get("type") == "water"
                            else "mdi:gas-cylinder"
                        ),
                        native_unit_of_measurement=channel.get("uom"),
                        sensor_id=f"{sensor_id}-{channel.get('channel')}",
                        state_class=SensorStateClass.MEASUREMENT,
                    ),
                )
                for sensor_id, sensor in service_location.sensors.items()
                for channel in sensor.channels
            ]
        )

        # Add today_energy_kwh sensors for switches
        entities.extend(
            [
                SmappeeSensor(
                    smappee_base=smappee_base,
                    service_location=service_location,
                    description=SmappeeSensorEntityDescription(
                        key="switch",
                        name=f"{actuator.name} - energy today",
                        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
                        sensor_id=actuator_id,
                        device_class=SensorDeviceClass.ENERGY,
                        state_class=SensorStateClass.TOTAL_INCREASING,
                    ),
                )
                for actuator_id, actuator in service_location.actuators.items()
                if actuator.type == "SWITCH" and not service_location.local_polling
            ]
        )

    async_add_entities(entities, True)