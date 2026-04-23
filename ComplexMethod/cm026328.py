def setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Set up the Monoprice Blackbird 4k 8x8 HDBaseT Matrix platform."""
    if DATA_BLACKBIRD not in hass.data:
        hass.data[DATA_BLACKBIRD] = {}

    port = config.get(CONF_PORT)
    host = config.get(CONF_HOST)

    connection = None
    if port is not None:
        try:
            blackbird = get_blackbird(port)
            connection = port
        except SerialException:
            _LOGGER.error("Error connecting to the Blackbird controller")
            return

    if host is not None:
        try:
            blackbird = get_blackbird(host, False)
            connection = host
        except TimeoutError:
            _LOGGER.error("Error connecting to the Blackbird controller")
            return

    sources = {
        source_id: extra[CONF_NAME] for source_id, extra in config[CONF_SOURCES].items()
    }

    devices = []
    for zone_id, extra in config[CONF_ZONES].items():
        _LOGGER.debug("Adding zone %d - %s", zone_id, extra[CONF_NAME])
        unique_id = f"{connection}-{zone_id}"
        device = BlackbirdZone(blackbird, sources, zone_id, extra[CONF_NAME])
        hass.data[DATA_BLACKBIRD][unique_id] = device
        devices.append(device)

    add_entities(devices, True)

    def service_handle(service: ServiceCall) -> None:
        """Handle for services."""
        entity_ids = service.data.get(ATTR_ENTITY_ID)
        source = service.data.get(ATTR_SOURCE)
        if entity_ids:
            devices = [
                device
                for device in hass.data[DATA_BLACKBIRD].values()
                if device.entity_id in entity_ids
            ]

        else:
            devices = hass.data[DATA_BLACKBIRD].values()

        for device in devices:
            if service.service == SERVICE_SETALLZONES:
                device.set_all_zones(source)

    hass.services.register(
        DOMAIN, SERVICE_SETALLZONES, service_handle, schema=BLACKBIRD_SETALLZONES_SCHEMA
    )