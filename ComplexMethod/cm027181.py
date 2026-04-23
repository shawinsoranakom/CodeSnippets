async def async_setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    async_add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Set up the REST binary sensor."""
    # Must update the sensor now (including fetching the rest resource) to
    # ensure it's updating its state.
    if discovery_info is not None:
        conf, coordinator, rest = await async_get_config_and_coordinator(
            hass, BINARY_SENSOR_DOMAIN, discovery_info
        )
    else:
        conf = config
        coordinator = None
        rest = create_rest_data_from_config(hass, conf)
        await rest.async_update(log_errors=False)

    if rest.data is None:
        if rest.last_exception:
            if isinstance(rest.last_exception, ssl.SSLError):
                _LOGGER.error(
                    "Error connecting %s failed with %s",
                    rest.url,
                    rest.last_exception,
                )
                return
            raise PlatformNotReady from rest.last_exception
        raise PlatformNotReady

    name = conf.get(CONF_NAME) or Template(DEFAULT_BINARY_SENSOR_NAME, hass)

    trigger_entity_config = {CONF_NAME: name}

    for key in TRIGGER_ENTITY_OPTIONS:
        if key not in conf:
            continue
        trigger_entity_config[key] = conf[key]

    async_add_entities(
        [
            RestBinarySensor(
                hass,
                coordinator,
                rest,
                conf,
                trigger_entity_config,
            )
        ],
    )