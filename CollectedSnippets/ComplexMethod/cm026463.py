async def async_setup_entry(
    hass: HomeAssistant,
    entry: SystemBridgeConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up System Bridge sensor based on a config entry."""
    coordinator = entry.runtime_data

    entities = [
        SystemBridgeSensor(coordinator, description, entry.data[CONF_PORT])
        for description in BASE_SENSOR_TYPES
    ]

    for index_device, device in enumerate(coordinator.data.disks.devices):
        if device.partitions is None:
            continue

        entities.extend(
            SystemBridgeSensor(
                coordinator,
                SystemBridgeSensorEntityDescription(
                    key=f"filesystem_{partition.mount_point.replace(':', '')}",
                    name=f"{partition.mount_point} space used",
                    state_class=SensorStateClass.MEASUREMENT,
                    native_unit_of_measurement=PERCENTAGE,
                    suggested_display_precision=2,
                    icon="mdi:harddisk",
                    value=(
                        lambda data, dk=index_device, pk=index_partition: (
                            partition_usage(data, dk, pk)
                        )
                    ),
                ),
                entry.data[CONF_PORT],
            )
            for index_partition, partition in enumerate(device.partitions)
        )

    if (
        coordinator.data.battery
        and coordinator.data.battery.percentage
        and coordinator.data.battery.percentage > -1
    ):
        entities.extend(
            SystemBridgeSensor(coordinator, description, entry.data[CONF_PORT])
            for description in BATTERY_SENSOR_TYPES
        )

    entities.append(
        SystemBridgeSensor(
            coordinator,
            SystemBridgeSensorEntityDescription(
                key="displays_connected",
                translation_key="displays_connected",
                state_class=SensorStateClass.MEASUREMENT,
                value=lambda data: len(data.displays) if data.displays else None,
            ),
            entry.data[CONF_PORT],
        )
    )

    if coordinator.data.displays is not None:
        for index, display in enumerate(coordinator.data.displays):
            entities = [
                *entities,
                SystemBridgeSensor(
                    coordinator,
                    SystemBridgeSensorEntityDescription(
                        key=f"display_{display.id}_resolution_x",
                        name=f"Display {display.id} resolution x",
                        state_class=SensorStateClass.MEASUREMENT,
                        native_unit_of_measurement=PIXELS,
                        icon="mdi:monitor",
                        value=lambda data, k=index: display_resolution_horizontal(
                            data, k
                        ),
                    ),
                    entry.data[CONF_PORT],
                ),
                SystemBridgeSensor(
                    coordinator,
                    SystemBridgeSensorEntityDescription(
                        key=f"display_{display.id}_resolution_y",
                        name=f"Display {display.id} resolution y",
                        state_class=SensorStateClass.MEASUREMENT,
                        native_unit_of_measurement=PIXELS,
                        icon="mdi:monitor",
                        value=lambda data, k=index: display_resolution_vertical(
                            data, k
                        ),
                    ),
                    entry.data[CONF_PORT],
                ),
                SystemBridgeSensor(
                    coordinator,
                    SystemBridgeSensorEntityDescription(
                        key=f"display_{display.id}_refresh_rate",
                        name=f"Display {display.id} refresh rate",
                        state_class=SensorStateClass.MEASUREMENT,
                        native_unit_of_measurement=UnitOfFrequency.HERTZ,
                        device_class=SensorDeviceClass.FREQUENCY,
                        suggested_display_precision=0,
                        icon="mdi:monitor",
                        value=lambda data, k=index: display_refresh_rate(data, k),
                    ),
                    entry.data[CONF_PORT],
                ),
            ]

    for index, gpu in enumerate(coordinator.data.gpus):
        entities.extend(
            [
                SystemBridgeSensor(
                    coordinator,
                    SystemBridgeSensorEntityDescription(
                        key=f"gpu_{gpu.id}_core_clock_speed",
                        name=f"{gpu.name} clock speed",
                        entity_registry_enabled_default=False,
                        state_class=SensorStateClass.MEASUREMENT,
                        native_unit_of_measurement=UnitOfFrequency.MEGAHERTZ,
                        device_class=SensorDeviceClass.FREQUENCY,
                        suggested_display_precision=0,
                        icon="mdi:speedometer",
                        value=lambda data, k=index: gpu_core_clock_speed(data, k),
                    ),
                    entry.data[CONF_PORT],
                ),
                SystemBridgeSensor(
                    coordinator,
                    SystemBridgeSensorEntityDescription(
                        key=f"gpu_{gpu.id}_memory_clock_speed",
                        name=f"{gpu.name} memory clock speed",
                        entity_registry_enabled_default=False,
                        state_class=SensorStateClass.MEASUREMENT,
                        native_unit_of_measurement=UnitOfFrequency.MEGAHERTZ,
                        device_class=SensorDeviceClass.FREQUENCY,
                        suggested_display_precision=0,
                        icon="mdi:speedometer",
                        value=lambda data, k=index: gpu_memory_clock_speed(data, k),
                    ),
                    entry.data[CONF_PORT],
                ),
                SystemBridgeSensor(
                    coordinator,
                    SystemBridgeSensorEntityDescription(
                        key=f"gpu_{gpu.id}_memory_free",
                        name=f"{gpu.name} memory free",
                        state_class=SensorStateClass.MEASUREMENT,
                        native_unit_of_measurement=UnitOfInformation.MEGABYTES,
                        device_class=SensorDeviceClass.DATA_SIZE,
                        suggested_display_precision=0,
                        icon="mdi:memory",
                        value=lambda data, k=index: gpu_memory_free(data, k),
                    ),
                    entry.data[CONF_PORT],
                ),
                SystemBridgeSensor(
                    coordinator,
                    SystemBridgeSensorEntityDescription(
                        key=f"gpu_{gpu.id}_memory_used_percentage",
                        name=f"{gpu.name} memory used %",
                        state_class=SensorStateClass.MEASUREMENT,
                        native_unit_of_measurement=PERCENTAGE,
                        suggested_display_precision=2,
                        icon="mdi:memory",
                        value=lambda data, k=index: gpu_memory_used_percentage(data, k),
                    ),
                    entry.data[CONF_PORT],
                ),
                SystemBridgeSensor(
                    coordinator,
                    SystemBridgeSensorEntityDescription(
                        key=f"gpu_{gpu.id}_memory_used",
                        name=f"{gpu.name} memory used",
                        entity_registry_enabled_default=False,
                        state_class=SensorStateClass.MEASUREMENT,
                        native_unit_of_measurement=UnitOfInformation.MEGABYTES,
                        device_class=SensorDeviceClass.DATA_SIZE,
                        suggested_display_precision=0,
                        icon="mdi:memory",
                        value=lambda data, k=index: gpu_memory_used(data, k),
                    ),
                    entry.data[CONF_PORT],
                ),
                SystemBridgeSensor(
                    coordinator,
                    SystemBridgeSensorEntityDescription(
                        key=f"gpu_{gpu.id}_fan_speed",
                        name=f"{gpu.name} fan speed",
                        entity_registry_enabled_default=False,
                        state_class=SensorStateClass.MEASUREMENT,
                        native_unit_of_measurement=REVOLUTIONS_PER_MINUTE,
                        icon="mdi:fan",
                        value=lambda data, k=index: gpu_fan_speed(data, k),
                    ),
                    entry.data[CONF_PORT],
                ),
                SystemBridgeSensor(
                    coordinator,
                    SystemBridgeSensorEntityDescription(
                        key=f"gpu_{gpu.id}_power_usage",
                        name=f"{gpu.name} power usage",
                        entity_registry_enabled_default=False,
                        state_class=SensorStateClass.MEASUREMENT,
                        native_unit_of_measurement=UnitOfPower.WATT,
                        value=lambda data, k=index: gpu_power_usage(data, k),
                    ),
                    entry.data[CONF_PORT],
                ),
                SystemBridgeSensor(
                    coordinator,
                    SystemBridgeSensorEntityDescription(
                        key=f"gpu_{gpu.id}_temperature",
                        name=f"{gpu.name} temperature",
                        entity_registry_enabled_default=False,
                        device_class=SensorDeviceClass.TEMPERATURE,
                        state_class=SensorStateClass.MEASUREMENT,
                        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
                        suggested_display_precision=2,
                        value=lambda data, k=index: gpu_temperature(data, k),
                    ),
                    entry.data[CONF_PORT],
                ),
                SystemBridgeSensor(
                    coordinator,
                    SystemBridgeSensorEntityDescription(
                        key=f"gpu_{gpu.id}_usage_percentage",
                        name=f"{gpu.name} usage %",
                        state_class=SensorStateClass.MEASUREMENT,
                        native_unit_of_measurement=PERCENTAGE,
                        suggested_display_precision=2,
                        icon="mdi:percent",
                        value=lambda data, k=index: gpu_usage_percentage(data, k),
                    ),
                    entry.data[CONF_PORT],
                ),
            ]
        )

    if coordinator.data.cpu.per_cpu is not None:
        for cpu in coordinator.data.cpu.per_cpu:
            entities.extend(
                [
                    SystemBridgeSensor(
                        coordinator,
                        SystemBridgeSensorEntityDescription(
                            key=f"processes_load_cpu_{cpu.id}",
                            name=f"Load CPU {cpu.id}",
                            entity_registry_enabled_default=False,
                            state_class=SensorStateClass.MEASUREMENT,
                            native_unit_of_measurement=PERCENTAGE,
                            icon="mdi:percent",
                            suggested_display_precision=2,
                            value=lambda data, k=cpu.id: cpu_usage_per_cpu(data, k),
                        ),
                        entry.data[CONF_PORT],
                    ),
                    SystemBridgeSensor(
                        coordinator,
                        SystemBridgeSensorEntityDescription(
                            key=f"cpu_power_core_{cpu.id}",
                            name=f"CPU Core {cpu.id} Power",
                            entity_registry_enabled_default=False,
                            native_unit_of_measurement=UnitOfPower.WATT,
                            state_class=SensorStateClass.MEASUREMENT,
                            icon="mdi:chip",
                            suggested_display_precision=2,
                            value=lambda data, k=cpu.id: cpu_power_per_cpu(data, k),
                        ),
                        entry.data[CONF_PORT],
                    ),
                ]
            )

    async_add_entities(entities)