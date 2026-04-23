async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: NutConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the NUT sensors."""
    valid_sensor_types: dict[str, SensorEntityDescription]

    pynut_data = config_entry.runtime_data
    coordinator = pynut_data.coordinator
    data = pynut_data.data
    unique_id = pynut_data.unique_id
    status = coordinator.data

    # Dynamically add outlet sensors to valid sensors dictionary
    if (num_outlets := status.get("outlet.count")) is not None:
        additional_sensor_types: dict[str, SensorEntityDescription] = {}
        for outlet_num in range(1, int(num_outlets) + 1):
            outlet_num_str: str = str(outlet_num)
            outlet_name: str = (
                status.get(f"outlet.{outlet_num_str}.name") or outlet_num_str
            )
            additional_sensor_types |= {
                f"outlet.{outlet_num_str}.current": SensorEntityDescription(
                    key=f"outlet.{outlet_num_str}.current",
                    translation_key="outlet_number_current",
                    translation_placeholders={"outlet_name": outlet_name},
                    native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
                    device_class=SensorDeviceClass.CURRENT,
                    state_class=SensorStateClass.MEASUREMENT,
                ),
                f"outlet.{outlet_num_str}.current_status": SensorEntityDescription(
                    key=f"outlet.{outlet_num_str}.current_status",
                    translation_key="outlet_number_current_status",
                    translation_placeholders={"outlet_name": outlet_name},
                    entity_category=EntityCategory.DIAGNOSTIC,
                    entity_registry_enabled_default=False,
                ),
                f"outlet.{outlet_num_str}.desc": SensorEntityDescription(
                    key=f"outlet.{outlet_num_str}.desc",
                    translation_key="outlet_number_desc",
                    translation_placeholders={"outlet_name": outlet_name},
                ),
                f"outlet.{outlet_num_str}.power": SensorEntityDescription(
                    key=f"outlet.{outlet_num_str}.power",
                    translation_key="outlet_number_power",
                    translation_placeholders={"outlet_name": outlet_name},
                    native_unit_of_measurement=UnitOfApparentPower.VOLT_AMPERE,
                    device_class=SensorDeviceClass.APPARENT_POWER,
                    state_class=SensorStateClass.MEASUREMENT,
                ),
                f"outlet.{outlet_num_str}.realpower": SensorEntityDescription(
                    key=f"outlet.{outlet_num_str}.realpower",
                    translation_key="outlet_number_realpower",
                    translation_placeholders={"outlet_name": outlet_name},
                    native_unit_of_measurement=UnitOfPower.WATT,
                    device_class=SensorDeviceClass.POWER,
                    state_class=SensorStateClass.MEASUREMENT,
                ),
            }

        valid_sensor_types = {**SENSOR_TYPES, **additional_sensor_types}
    else:
        valid_sensor_types = SENSOR_TYPES

    # If device reports ambient sensors are not present, then remove
    has_ambient_sensors: bool = status.get(AMBIENT_PRESENT) != "no"
    resources = [
        sensor_id
        for sensor_id in valid_sensor_types
        if sensor_id in status
        and (has_ambient_sensors or sensor_id not in AMBIENT_SENSORS)
    ]

    # Display status is a special case that falls back to the status value
    # of the UPS instead.
    if KEY_STATUS in status:
        resources.append(KEY_STATUS_DISPLAY)

    async_add_entities(
        NUTSensor(
            coordinator,
            valid_sensor_types[sensor_type],
            data,
            unique_id,
        )
        for sensor_type in resources
    )