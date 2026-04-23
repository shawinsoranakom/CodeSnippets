async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ScreenLogicConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up entry."""
    coordinator = config_entry.runtime_data
    gateway = coordinator.gateway

    entities: list[ScreenLogicSensor] = [
        ScreenLogicPushSensor(coordinator, core_sensor_description)
        for core_sensor_description in SUPPORTED_CORE_SENSORS
        if (
            gateway.get_data(
                *core_sensor_description.data_root, core_sensor_description.key
            )
            is not None
        )
    ]

    for pump_index, pump_data in gateway.get_data(DEVICE.PUMP).items():
        if not pump_data or not pump_data.get(VALUE.DATA):
            continue
        pump_type = pump_data[VALUE.TYPE]
        for proto_pump_sensor_description in SUPPORTED_PUMP_SENSORS:
            if not pump_data.get(proto_pump_sensor_description.key):
                continue
            entities.append(
                ScreenLogicPumpSensor(
                    coordinator,
                    copy(proto_pump_sensor_description),
                    pump_index,
                    pump_type,
                )
            )

    chem_sensor_description: ScreenLogicPushSensorDescription
    for chem_sensor_description in SUPPORTED_INTELLICHEM_SENSORS:
        chem_sensor_data_path = (
            *chem_sensor_description.data_root,
            chem_sensor_description.key,
        )
        if EQUIPMENT_FLAG.INTELLICHEM not in gateway.equipment_flags:
            cleanup_excluded_entity(coordinator, SENSOR_DOMAIN, chem_sensor_data_path)
            continue
        if gateway.get_data(*chem_sensor_data_path):
            chem_sensor_description = dataclasses.replace(
                chem_sensor_description, entity_category=EntityCategory.DIAGNOSTIC
            )
            entities.append(ScreenLogicPushSensor(coordinator, chem_sensor_description))

    scg_sensor_description: ScreenLogicSensorDescription
    for scg_sensor_description in SUPPORTED_SCG_SENSORS:
        scg_sensor_data_path = (
            *scg_sensor_description.data_root,
            scg_sensor_description.key,
        )
        if EQUIPMENT_FLAG.CHLORINATOR not in gateway.equipment_flags:
            cleanup_excluded_entity(coordinator, SENSOR_DOMAIN, scg_sensor_data_path)
            continue
        if gateway.get_data(*scg_sensor_data_path):
            scg_sensor_description = dataclasses.replace(
                scg_sensor_description, entity_category=EntityCategory.DIAGNOSTIC
            )
            entities.append(ScreenLogicSensor(coordinator, scg_sensor_description))

    async_add_entities(entities)