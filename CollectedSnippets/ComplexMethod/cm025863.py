async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the Compensation sensor."""
    hass.data[DATA_COMPENSATION] = {}

    for compensation, conf in config[DOMAIN].items():
        _LOGGER.debug("Setup %s.%s", DOMAIN, compensation)

        degree = conf[CONF_DEGREE]

        initial_coefficients: list[tuple[float, float]] = conf[CONF_DATAPOINTS]
        sorted_coefficients = sorted(initial_coefficients, key=itemgetter(0))

        # get x values and y values from the x,y point pairs
        x_values, y_values = zip(*initial_coefficients, strict=False)

        # try to get valid coefficients for a polynomial
        coefficients = None
        with np.errstate(all="raise"):
            try:
                coefficients = np.polyfit(x_values, y_values, degree)
            except FloatingPointError as error:
                _LOGGER.error(
                    "Setup of %s encountered an error, %s",
                    compensation,
                    error,
                )

        if coefficients is not None:
            data = {
                k: v for k, v in conf.items() if k not in [CONF_DEGREE, CONF_DATAPOINTS]
            }
            data[CONF_POLYNOMIAL] = np.poly1d(coefficients)

            if data[CONF_LOWER_LIMIT]:
                data[CONF_MINIMUM] = sorted_coefficients[0]
            else:
                data[CONF_MINIMUM] = None

            if data[CONF_UPPER_LIMIT]:
                data[CONF_MAXIMUM] = sorted_coefficients[-1]
            else:
                data[CONF_MAXIMUM] = None

            hass.data[DATA_COMPENSATION][compensation] = data

            hass.async_create_task(
                async_load_platform(
                    hass,
                    SENSOR_DOMAIN,
                    DOMAIN,
                    {CONF_COMPENSATION: compensation},
                    config,
                )
            )

    return True