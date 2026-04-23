def setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Set up the aREST sensor."""
    resource = config[CONF_RESOURCE]
    var_conf = config[CONF_MONITORED_VARIABLES]
    pins = config[CONF_PINS]

    try:
        response = requests.get(resource, timeout=10).json()
    except requests.exceptions.MissingSchema:
        _LOGGER.error(
            "Missing resource or schema in configuration. Add http:// to your URL"
        )
        return
    except requests.exceptions.ConnectionError:
        _LOGGER.error("No route to device at %s", resource)
        return

    arest = ArestData(resource)

    def make_renderer(value_template):
        """Create a renderer based on variable_template value."""
        if value_template is None:
            return lambda value: value

        def _render(value):
            try:
                return value_template.async_render({"value": value}, parse_result=False)
            except TemplateError:
                _LOGGER.exception("Error parsing value")
                return value

        return _render

    dev = []

    if var_conf is not None:
        for variable, var_data in var_conf.items():
            if variable not in response["variables"]:
                _LOGGER.error("Variable: %s does not exist", variable)
                continue

            renderer = make_renderer(var_data.get(CONF_VALUE_TEMPLATE))
            dev.append(
                ArestSensor(
                    arest,
                    resource,
                    config.get(CONF_NAME, response[CONF_NAME]),
                    var_data.get(CONF_NAME, variable),
                    variable=variable,
                    unit_of_measurement=var_data.get(CONF_UNIT_OF_MEASUREMENT),
                    renderer=renderer,
                )
            )

    if pins is not None:
        for pinnum, pin in pins.items():
            renderer = make_renderer(pin.get(CONF_VALUE_TEMPLATE))
            dev.append(
                ArestSensor(
                    ArestData(resource, pinnum),
                    resource,
                    config.get(CONF_NAME, response[CONF_NAME]),
                    pin.get(CONF_NAME),
                    pin=pinnum,
                    unit_of_measurement=pin.get(CONF_UNIT_OF_MEASUREMENT),
                    renderer=renderer,
                )
            )

    add_entities(dev, True)