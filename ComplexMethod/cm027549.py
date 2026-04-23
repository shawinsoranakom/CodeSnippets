async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Yeelight from a config entry."""
    custom_effects = _parse_custom_effects(hass.data[DOMAIN][DATA_CUSTOM_EFFECTS])

    device = hass.data[DOMAIN][DATA_CONFIG_ENTRIES][config_entry.entry_id][DATA_DEVICE]
    _LOGGER.debug("Adding %s", device.name)

    nl_switch_light = device.config.get(CONF_NIGHTLIGHT_SWITCH)

    lights = []

    device_type = device.type

    def _lights_setup_helper(klass):
        lights.append(klass(device, config_entry, custom_effects=custom_effects))

    if device_type == BulbType.White:
        _lights_setup_helper(YeelightGenericLight)
    elif device_type == BulbType.Color:
        if nl_switch_light and device.is_nightlight_supported:
            _lights_setup_helper(YeelightColorLightWithNightlightSwitch)
            _lights_setup_helper(YeelightNightLightModeWithoutBrightnessControl)
        else:
            _lights_setup_helper(YeelightColorLightWithoutNightlightSwitchLight)
    elif device_type == BulbType.WhiteTemp:
        if nl_switch_light and device.is_nightlight_supported:
            _lights_setup_helper(YeelightWithNightLight)
            _lights_setup_helper(YeelightNightLightMode)
        else:
            _lights_setup_helper(YeelightWhiteTempWithoutNightlightSwitch)
    elif device_type == BulbType.WhiteTempMood:
        if nl_switch_light and device.is_nightlight_supported:
            _lights_setup_helper(YeelightNightLightModeWithAmbientSupport)
            _lights_setup_helper(YeelightWithAmbientAndNightlight)
        else:
            _lights_setup_helper(YeelightWithAmbientWithoutNightlight)
        _lights_setup_helper(YeelightAmbientLight)
    else:
        _lights_setup_helper(YeelightGenericLight)
        _LOGGER.warning(
            "Cannot determine device type for %s, %s. Falling back to white only",
            device.host,
            device.name,
        )

    async_add_entities(lights)
    _async_setup_services(hass)