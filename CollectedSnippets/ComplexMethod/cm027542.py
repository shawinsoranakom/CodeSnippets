def setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Set up the Ziggo Mediabox XL platform."""

    hass.data[DATA_KNOWN_DEVICES] = known_devices = set()

    # Is this a manual configuration?
    if (host := config.get(CONF_HOST)) is not None:
        name = config.get(CONF_NAME)
        manual_config = True
    elif discovery_info is not None:
        host = discovery_info["host"]
        name = discovery_info.get("name")
        manual_config = False
    else:
        _LOGGER.error("Cannot determine device")
        return

    # Only add a device once, so discovered devices do not override manual
    # config.
    hosts = []
    connection_successful = False
    ip_addr = socket.gethostbyname(host)
    if ip_addr not in known_devices:
        try:
            # Mediabox instance with a timeout of 3 seconds.
            mediabox = ZiggoMediaboxXL(ip_addr, 3)
            # Check if a connection can be established to the device.
            if mediabox.test_connection():
                connection_successful = True
            elif manual_config:
                _LOGGER.error("Can't connect to %s", host)
            else:
                _LOGGER.error("Can't connect to %s", host)
            # When the device is in eco mode it's not connected to the network
            # so it needs to be added anyway if it's configured manually.
            if manual_config or connection_successful:
                hosts.append(
                    ZiggoMediaboxXLDevice(mediabox, host, name, connection_successful)
                )
                known_devices.add(ip_addr)
        except OSError as error:
            _LOGGER.error("Can't connect to %s: %s", host, error)
    else:
        _LOGGER.warning("Ignoring duplicate Ziggo Mediabox XL %s", host)
    add_entities(hosts, True)