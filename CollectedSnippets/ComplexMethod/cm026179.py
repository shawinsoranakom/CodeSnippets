def setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Set up the configured Numato USB GPIO switch ports."""
    if discovery_info is None:
        return

    api = hass.data[DOMAIN][DATA_API]
    switches = []
    devices = hass.data[DOMAIN][CONF_DEVICES]
    for device in [d for d in devices if CONF_SWITCHES in d]:
        device_id = device[CONF_ID]
        platform = device[CONF_SWITCHES]
        invert_logic = platform[CONF_INVERT_LOGIC]
        ports = platform[CONF_PORTS]
        for port, port_name in ports.items():
            try:
                api.setup_output(device_id, port)
                api.write_output(device_id, port, 1 if invert_logic else 0)
            except NumatoGpioError as err:
                _LOGGER.error(
                    "Failed to initialize switch '%s' on Numato device %s port %s: %s",
                    port_name,
                    device_id,
                    port,
                    err,
                )
                continue
            switches.append(
                NumatoGpioSwitch(
                    port_name,
                    device_id,
                    port,
                    invert_logic,
                    api,
                )
            )
    add_entities(switches, True)