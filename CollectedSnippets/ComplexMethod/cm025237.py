async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: XiaomiMiioConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the Xiaomi sensor from a config entry."""
    entities = []

    if config_entry.data[CONF_FLOW_TYPE] == CONF_DEVICE:
        model = config_entry.data[CONF_MODEL]
        sensors: Iterable[str] = []
        if model in MODEL_AIRFRESH_A1 or model in MODEL_AIRFRESH_T2017:
            sensors = AIRFRESH_A1_BINARY_SENSORS
        elif model in MODEL_FAN_ZA5:
            sensors = FAN_ZA5_BINARY_SENSORS
        elif model in MODELS_HUMIDIFIER_MIIO:
            sensors = HUMIDIFIER_MIIO_BINARY_SENSORS
        elif model in MODELS_HUMIDIFIER_MIOT:
            sensors = HUMIDIFIER_MIOT_BINARY_SENSORS
        elif model in MODELS_HUMIDIFIER_MJJSQ:
            sensors = HUMIDIFIER_MJJSQ_BINARY_SENSORS
        elif model in MODELS_VACUUM:
            _setup_vacuum_sensors(hass, config_entry, async_add_entities)
            return

        for description in BINARY_SENSOR_TYPES:
            if description.key not in sensors:
                continue
            entities.append(
                XiaomiGenericBinarySensor(
                    config_entry.runtime_data.device,
                    config_entry,
                    f"{description.key}_{config_entry.unique_id}",
                    config_entry.runtime_data.device_coordinator,
                    description,
                )
            )

    async_add_entities(entities)