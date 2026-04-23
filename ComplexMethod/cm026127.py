def setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Set up the LaCrosse sensors."""
    usb_device: str = config[CONF_DEVICE]
    baud: int = config[CONF_BAUD]
    expire_after: int | None = config.get(CONF_EXPIRE_AFTER)

    _LOGGER.debug("%s %s", usb_device, baud)

    try:
        lacrosse = pylacrosse.LaCrosse(usb_device, baud)
        lacrosse.open()
    except SerialException as exc:
        _LOGGER.warning("Unable to open serial port: %s", exc)
        return

    hass.bus.listen_once(EVENT_HOMEASSISTANT_STOP, lambda event: lacrosse.close())

    if CONF_JEELINK_LED in config:
        lacrosse.led_mode_state(config.get(CONF_JEELINK_LED))
    if CONF_FREQUENCY in config:
        lacrosse.set_frequency(config.get(CONF_FREQUENCY))
    if CONF_DATARATE in config:
        lacrosse.set_datarate(config.get(CONF_DATARATE))
    if CONF_TOGGLE_INTERVAL in config:
        lacrosse.set_toggle_interval(config.get(CONF_TOGGLE_INTERVAL))
    if CONF_TOGGLE_MASK in config:
        lacrosse.set_toggle_mask(config.get(CONF_TOGGLE_MASK))

    lacrosse.start_scan()

    sensors: list[LaCrosseSensor] = []
    for device, device_config in config[CONF_SENSORS].items():
        _LOGGER.debug("%s %s", device, device_config)

        typ: str = device_config[CONF_TYPE]
        sensor_class = TYPE_CLASSES[typ]
        name: str = device_config.get(CONF_NAME, device)

        sensors.append(
            sensor_class(hass, lacrosse, device, name, expire_after, device_config)
        )

    add_entities(sensors)