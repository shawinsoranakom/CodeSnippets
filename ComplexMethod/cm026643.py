def setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Set up the Tellstick sensors."""

    sensor_value_descriptions = {
        tellcore_constants.TELLSTICK_TEMPERATURE: DatatypeDescription(
            "temperature",
            config.get(CONF_TEMPERATURE_SCALE),
            SensorDeviceClass.TEMPERATURE,
        ),
        tellcore_constants.TELLSTICK_HUMIDITY: DatatypeDescription(
            "humidity",
            PERCENTAGE,
            SensorDeviceClass.HUMIDITY,
        ),
        tellcore_constants.TELLSTICK_RAINRATE: DatatypeDescription(
            "rain rate", "", None
        ),
        tellcore_constants.TELLSTICK_RAINTOTAL: DatatypeDescription(
            "rain total", "", None
        ),
        tellcore_constants.TELLSTICK_WINDDIRECTION: DatatypeDescription(
            "wind direction", "", None
        ),
        tellcore_constants.TELLSTICK_WINDAVERAGE: DatatypeDescription(
            "wind average", "", None
        ),
        tellcore_constants.TELLSTICK_WINDGUST: DatatypeDescription(
            "wind gust", "", None
        ),
    }

    try:
        tellcore_lib = telldus.TelldusCore()
    except OSError:
        _LOGGER.exception("Could not initialize Tellstick")
        return

    sensors = []
    datatype_mask = config.get(CONF_DATATYPE_MASK)

    if config[CONF_ONLY_NAMED]:
        named_sensors = {}
        for named_sensor in config[CONF_ONLY_NAMED]:
            name = named_sensor[CONF_NAME]
            proto = named_sensor.get(CONF_PROTOCOL)
            model = named_sensor.get(CONF_MODEL)
            id_ = named_sensor[CONF_ID]
            if proto is not None:
                if model is not None:
                    named_sensors[f"{proto}{model}{id_}"] = name
                else:
                    named_sensors[f"{proto}{id_}"] = name
            else:
                named_sensors[id_] = name

    for tellcore_sensor in tellcore_lib.sensors():
        if not config[CONF_ONLY_NAMED]:
            sensor_name = str(tellcore_sensor.id)
        else:
            proto_id = f"{tellcore_sensor.protocol}{tellcore_sensor.id}"
            proto_model_id = (
                f"{tellcore_sensor.protocol}{tellcore_sensor.model}{tellcore_sensor.id}"
            )
            if tellcore_sensor.id in named_sensors:
                sensor_name = named_sensors[tellcore_sensor.id]
            elif proto_id in named_sensors:
                sensor_name = named_sensors[proto_id]
            elif proto_model_id in named_sensors:
                sensor_name = named_sensors[proto_model_id]
            else:
                continue

        for datatype, sensor_info in sensor_value_descriptions.items():
            if datatype & datatype_mask and tellcore_sensor.has_value(datatype):
                sensors.append(
                    TellstickSensor(sensor_name, tellcore_sensor, datatype, sensor_info)
                )

    add_entities(sensors)