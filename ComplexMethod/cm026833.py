def get_accessory(  # noqa: C901
    hass: HomeAssistant, driver: HomeDriver, state: State, aid: int | None, config: dict
) -> HomeAccessory | None:
    """Take state and return an accessory object if supported."""
    if not aid:
        _LOGGER.warning(
            (
                'The entity "%s" is not supported, since it '
                "generates an invalid aid, please change it"
            ),
            state.entity_id,
        )
        return None

    a_type = None
    name = config.get(CONF_NAME, state.name)
    features = state.attributes.get(ATTR_SUPPORTED_FEATURES, 0)

    if state.domain == "alarm_control_panel":
        a_type = "SecuritySystem"

    elif state.domain in ("binary_sensor", "device_tracker", "person"):
        a_type = "BinarySensor"

    elif state.domain == "climate":
        a_type = "Thermostat"

    elif state.domain == "cover":
        device_class = state.attributes.get(ATTR_DEVICE_CLASS)

        if device_class in (
            CoverDeviceClass.GARAGE,
            CoverDeviceClass.GATE,
        ) and features & (CoverEntityFeature.OPEN | CoverEntityFeature.CLOSE):
            a_type = "GarageDoorOpener"
        elif (
            device_class == CoverDeviceClass.WINDOW
            and features & CoverEntityFeature.SET_POSITION
        ):
            a_type = "Window"
        elif (
            device_class == CoverDeviceClass.DOOR
            and features & CoverEntityFeature.SET_POSITION
        ):
            a_type = "Door"
        elif features & CoverEntityFeature.SET_POSITION:
            a_type = "WindowCovering"
        elif features & (CoverEntityFeature.OPEN | CoverEntityFeature.CLOSE):
            a_type = "WindowCoveringBasic"
        elif features & CoverEntityFeature.SET_TILT_POSITION:
            # WindowCovering and WindowCoveringBasic both support tilt
            # only WindowCovering can handle the covers that are missing
            # CoverEntityFeature.SET_POSITION, CoverEntityFeature.OPEN,
            # and CoverEntityFeature.CLOSE
            a_type = "WindowCovering"

    elif state.domain == "fan":
        if fan_type := config.get(CONF_TYPE):
            a_type = FAN_TYPES[fan_type]
        else:
            a_type = "Fan"

    elif state.domain == "humidifier":
        a_type = "HumidifierDehumidifier"

    elif state.domain == "light":
        a_type = "Light"

    elif state.domain == "lock":
        a_type = "Lock"

    elif state.domain == "media_player":
        device_class = state.attributes.get(ATTR_DEVICE_CLASS)
        feature_list = config.get(CONF_FEATURE_LIST, [])

        if device_class == MediaPlayerDeviceClass.RECEIVER:
            a_type = "ReceiverMediaPlayer"
        elif device_class == MediaPlayerDeviceClass.TV:
            a_type = "TelevisionMediaPlayer"
        elif validate_media_player_features(state, feature_list):
            a_type = "MediaPlayer"

    elif state.domain == "sensor":
        device_class = state.attributes.get(ATTR_DEVICE_CLASS)
        unit = state.attributes.get(ATTR_UNIT_OF_MEASUREMENT)

        if device_class == SensorDeviceClass.TEMPERATURE or unit in (
            UnitOfTemperature.CELSIUS,
            UnitOfTemperature.FAHRENHEIT,
        ):
            a_type = "TemperatureSensor"
        elif device_class == SensorDeviceClass.HUMIDITY and unit == PERCENTAGE:
            a_type = "HumiditySensor"
        elif device_class == SensorDeviceClass.PM10:
            a_type = "PM10Sensor"
        elif device_class == SensorDeviceClass.PM25:
            a_type = "PM25Sensor"
        elif device_class == SensorDeviceClass.NITROGEN_DIOXIDE:
            a_type = "NitrogenDioxideSensor"
        elif device_class == SensorDeviceClass.VOLATILE_ORGANIC_COMPOUNDS:
            a_type = "VolatileOrganicCompoundsSensor"
        elif device_class == SensorDeviceClass.GAS:
            a_type = "AirQualitySensor"
        elif device_class == SensorDeviceClass.CO:
            a_type = "CarbonMonoxideSensor"
        elif device_class == SensorDeviceClass.CO2:
            a_type = "CarbonDioxideSensor"
        elif device_class == SensorDeviceClass.ILLUMINANCE or unit == LIGHT_LUX:
            a_type = "LightSensor"

        # Fallbacks based on entity_id
        elif SensorDeviceClass.PM10 in state.entity_id:
            a_type = "PM10Sensor"
        elif SensorDeviceClass.PM25 in state.entity_id:
            a_type = "PM25Sensor"
        elif SensorDeviceClass.GAS in state.entity_id:
            a_type = "AirQualitySensor"
        elif "co2" in state.entity_id:
            a_type = "CarbonDioxideSensor"

        else:
            _LOGGER.debug(
                "%s: Unsupported sensor type (device_class=%s) (unit=%s)",
                state.entity_id,
                device_class,
                unit,
            )

    elif state.domain == "switch":
        if switch_type := config.get(CONF_TYPE):
            a_type = SWITCH_TYPES[switch_type]
        elif state.attributes.get(ATTR_DEVICE_CLASS) == SwitchDeviceClass.OUTLET:
            a_type = "Outlet"
        else:
            a_type = "Switch"

    elif state.domain == "valve":
        a_type = "Valve"

    elif state.domain == "vacuum":
        a_type = "Vacuum"

    elif (
        state.domain == "lawn_mower"
        and features & LawnMowerEntityFeature.DOCK
        and features & LawnMowerEntityFeature.START_MOWING
    ):
        a_type = "LawnMower"

    elif state.domain == "remote" and features & RemoteEntityFeature.ACTIVITY:
        a_type = "ActivityRemote"

    elif state.domain in (
        "automation",
        "button",
        "input_boolean",
        "input_button",
        "remote",
        "scene",
        "script",
    ):
        a_type = "Switch"

    elif state.domain in ("input_select", "select"):
        a_type = "SelectSwitch"

    elif state.domain == "water_heater":
        a_type = "WaterHeater"

    elif state.domain == "camera":
        a_type = "Camera"

    if a_type is None:
        return None

    _LOGGER.debug('Add "%s" as "%s"', state.entity_id, a_type)
    return TYPES[a_type](hass, driver, name, state.entity_id, aid, config)