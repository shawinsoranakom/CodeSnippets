async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ScreenLogicConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up entry."""
    coordinator = config_entry.runtime_data
    gateway = coordinator.gateway

    entities: list[ScreenLogicBinarySensor] = [
        ScreenLogicPushBinarySensor(coordinator, core_sensor_description)
        for core_sensor_description in SUPPORTED_CORE_SENSORS
        if (
            gateway.get_data(
                *core_sensor_description.data_root, core_sensor_description.key
            )
            is not None
        )
    ]

    for p_index, p_data in gateway.get_data(DEVICE.PUMP).items():
        if not p_data or not p_data.get(VALUE.DATA):
            continue
        entities.extend(
            ScreenLogicPumpBinarySensor(
                coordinator, copy(proto_pump_sensor_description), p_index
            )
            for proto_pump_sensor_description in SUPPORTED_PUMP_SENSORS
        )

    chem_sensor_description: ScreenLogicPushBinarySensorDescription
    for chem_sensor_description in SUPPORTED_INTELLICHEM_SENSORS:
        chem_sensor_data_path = (
            *chem_sensor_description.data_root,
            chem_sensor_description.key,
        )
        if EQUIPMENT_FLAG.INTELLICHEM not in gateway.equipment_flags:
            cleanup_excluded_entity(
                coordinator, BINARY_SENSOR_DOMAIN, chem_sensor_data_path
            )
            continue
        if gateway.get_data(*chem_sensor_data_path):
            entities.append(
                ScreenLogicPushBinarySensor(coordinator, chem_sensor_description)
            )

    scg_sensor_description: ScreenLogicBinarySensorDescription
    for scg_sensor_description in SUPPORTED_SCG_SENSORS:
        scg_sensor_data_path = (
            *scg_sensor_description.data_root,
            scg_sensor_description.key,
        )
        if EQUIPMENT_FLAG.CHLORINATOR not in gateway.equipment_flags:
            cleanup_excluded_entity(
                coordinator, BINARY_SENSOR_DOMAIN, scg_sensor_data_path
            )
            continue
        if gateway.get_data(*scg_sensor_data_path):
            entities.append(
                ScreenLogicBinarySensor(coordinator, scg_sensor_description)
            )

    async_add_entities(entities)