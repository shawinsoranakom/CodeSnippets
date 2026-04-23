def setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the Join services."""
    for device in config[DOMAIN]:
        api_key = device.get(CONF_API_KEY)
        device_id = device.get(CONF_DEVICE_ID)
        device_ids = device.get(CONF_DEVICE_IDS)
        device_names = device.get(CONF_DEVICE_NAMES)
        name = device.get(CONF_NAME)
        name = f"{name.lower().replace(' ', '_')}_" if name else ""
        if api_key and not get_devices(api_key):
            _LOGGER.error("Error connecting to Join, check API key")
            return False
        if device_id is None and device_ids is None and device_names is None:
            _LOGGER.error(
                "No device was provided. Please specify device_id"
                ", device_ids, or device_names"
            )
            return False

        register_device(hass, api_key, name, device_id, device_ids, device_names)
    return True