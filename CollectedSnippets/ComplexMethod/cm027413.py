async def async_setup_entry(
    hass: HomeAssistant,
    entry: HomeWizardConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Initialize sensors."""

    # Initialize default sensors
    entities: list = [
        HomeWizardSensorEntity(entry.runtime_data, description)
        for description in SENSORS
        if description.has_fn(entry.runtime_data.data)
    ]
    # Add optional production power sensor for supported energy monitoring devices
    # or plug-in battery
    if entry.runtime_data.data.device.product_type in (
        Model.ENERGY_SOCKET,
        Model.ENERGY_METER_1_PHASE,
        Model.ENERGY_METER_3_PHASE,
        Model.ENERGY_METER_EASTRON_SDM230,
        Model.ENERGY_METER_EASTRON_SDM630,
        Model.BATTERY,
    ):
        active_prodution_power_sensor_description = HomeWizardSensorEntityDescription(
            key="active_production_power_w",
            translation_key="active_production_power_w",
            native_unit_of_measurement=UnitOfPower.WATT,
            device_class=SensorDeviceClass.POWER,
            state_class=SensorStateClass.MEASUREMENT,
            suggested_display_precision=0,
            entity_registry_enabled_default=(
                entry.runtime_data.data.device.product_type == Model.BATTERY
                or (
                    (
                        total_export
                        := entry.runtime_data.data.measurement.energy_export_kwh
                    )
                    is not None
                    and total_export > 0
                )
            ),
            has_fn=lambda x: True,
            value_fn=lambda data: (
                power_w * -1 if (power_w := data.measurement.power_w) else power_w
            ),
        )
        entities.append(
            HomeWizardSensorEntity(
                entry.runtime_data, active_prodution_power_sensor_description
            )
        )

    # Initialize external devices
    measurement = entry.runtime_data.data.measurement
    if measurement.external_devices is not None:
        for unique_id, device in measurement.external_devices.items():
            if device.type is not None and (
                description := EXTERNAL_SENSORS.get(device.type)
            ):
                # Add external device
                entities.append(
                    HomeWizardExternalSensorEntity(
                        entry.runtime_data, description, unique_id
                    )
                )

    async_add_entities(entities)