def setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Set up the configured Numato USB GPIO binary sensor ports."""
    if discovery_info is None:
        return

    def read_gpio(device_id: int, port: int, level: bool) -> None:
        """Send signal to entity to have it update state."""
        dispatcher_send(hass, NUMATO_SIGNAL.format(device_id, port), level)

    api = hass.data[DOMAIN][DATA_API]
    binary_sensors = []
    devices = hass.data[DOMAIN][CONF_DEVICES]
    for device in [d for d in devices if CONF_BINARY_SENSORS in d]:
        device_id = device[CONF_ID]
        platform = device[CONF_BINARY_SENSORS]
        invert_logic = platform[CONF_INVERT_LOGIC]
        ports = platform[CONF_PORTS]
        for port, port_name in ports.items():
            try:
                api.setup_input(device_id, port)

            except NumatoGpioError as err:
                _LOGGER.error(
                    (
                        "Failed to initialize binary sensor '%s' on Numato device %s"
                        " port %s: %s"
                    ),
                    port_name,
                    device_id,
                    port,
                    err,
                )
                continue
            try:
                api.edge_detect(device_id, port, partial(read_gpio, device_id))

            except NumatoGpioError as err:
                _LOGGER.error(
                    "Notification setup failed on device %s, "
                    "updates on binary sensor %s only in polling mode: %s",
                    device_id,
                    port_name,
                    err,
                )
            binary_sensors.append(
                NumatoGpioBinarySensor(
                    port_name,
                    device_id,
                    port,
                    invert_logic,
                    api,
                )
            )
    add_entities(binary_sensors, True)