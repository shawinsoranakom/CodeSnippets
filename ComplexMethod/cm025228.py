async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: XiaomiMiioConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the Xiaomi sensor from a config entry."""
    entities: list[SensorEntity] = []

    if config_entry.data[CONF_FLOW_TYPE] == CONF_GATEWAY:
        gateway = config_entry.runtime_data.gateway
        gateway_coordinators = config_entry.runtime_data.gateway_coordinators
        # Gateway illuminance sensor
        if gateway.model not in [
            GATEWAY_MODEL_AC_V1,
            GATEWAY_MODEL_AC_V2,
            GATEWAY_MODEL_AC_V3,
            GATEWAY_MODEL_AQARA,
            GATEWAY_MODEL_EU,
        ]:
            description = SENSOR_TYPES[ATTR_ILLUMINANCE]
            entities.append(
                XiaomiGatewayIlluminanceSensor(
                    gateway, config_entry.title, config_entry.unique_id, description
                )
            )
        # Gateway sub devices
        sub_devices = gateway.devices
        for sub_device in sub_devices.values():
            for sensor, description in SENSOR_TYPES.items():
                if sensor not in sub_device.status:
                    continue
                entities.append(
                    XiaomiGatewaySensor(
                        gateway_coordinators[sub_device.sid], description
                    )
                )
    elif config_entry.data[CONF_FLOW_TYPE] == CONF_DEVICE:
        device: MiioDevice
        host = config_entry.data[CONF_HOST]
        token = config_entry.data[CONF_TOKEN]
        model: str = config_entry.data[CONF_MODEL]

        if model in (MODEL_FAN_ZA1, MODEL_FAN_ZA3, MODEL_FAN_ZA4, MODEL_FAN_P5):
            return

        if model in MODELS_AIR_QUALITY_MONITOR:
            unique_id = config_entry.unique_id
            name = config_entry.title
            _LOGGER.debug("Initializing with host %s (token %s...)", host, token[:5])

            device = AirQualityMonitor(host, token)
            description = SENSOR_TYPES[ATTR_AIR_QUALITY]
            entities.append(
                XiaomiAirQualityMonitor(
                    name, device, config_entry, unique_id, description
                )
            )
        else:
            device = config_entry.runtime_data.device
            coordinator = config_entry.runtime_data.device_coordinator
            sensors: Iterable[str] = []
            if model in MODEL_TO_SENSORS_MAP:
                sensors = MODEL_TO_SENSORS_MAP[model]
            elif model in MODELS_HUMIDIFIER_MIOT:
                sensors = HUMIDIFIER_MIOT_SENSORS
            elif model in MODELS_HUMIDIFIER_MJJSQ:
                sensors = HUMIDIFIER_MJJSQ_SENSORS
            elif model in MODELS_HUMIDIFIER_MIIO:
                sensors = HUMIDIFIER_MIIO_SENSORS
            elif model in MODELS_PURIFIER_MIIO:
                sensors = PURIFIER_MIIO_SENSORS
            elif model in MODELS_PURIFIER_MIOT:
                sensors = PURIFIER_MIOT_SENSORS
            elif model in MODELS_VACUUM or model.startswith(
                (ROBOROCK_GENERIC, ROCKROBO_GENERIC)
            ):
                _setup_vacuum_sensors(hass, config_entry, async_add_entities)
                return

            for sensor, description in SENSOR_TYPES.items():
                if sensor not in sensors:
                    continue
                entities.append(
                    XiaomiGenericSensor(
                        device,
                        config_entry,
                        f"{sensor}_{config_entry.unique_id}",
                        coordinator,
                        description,
                    )
                )

    async_add_entities(entities)