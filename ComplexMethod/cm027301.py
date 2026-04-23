def validate_sensor_state_and_device_class_config(config: ConfigType) -> ConfigType:
    """Validate the sensor options, state and device class config."""
    if (
        CONF_LAST_RESET_VALUE_TEMPLATE in config
        and (state_class := config.get(CONF_STATE_CLASS)) != SensorStateClass.TOTAL
    ):
        raise vol.Invalid(
            f"The option `{CONF_LAST_RESET_VALUE_TEMPLATE}` cannot be used "
            f"together with state class `{state_class}`"
        )

    unit_of_measurement: str | None
    if (
        unit_of_measurement := config.get(CONF_UNIT_OF_MEASUREMENT)
    ) is not None and not unit_of_measurement.strip():
        config.pop(CONF_UNIT_OF_MEASUREMENT)

    # Only allow `options` to be set for `enum` sensors
    # to limit the possible sensor values
    if (options := config.get(CONF_OPTIONS)) is not None:
        if not options:
            raise vol.Invalid("An empty options list is not allowed")
        if config.get(CONF_STATE_CLASS) or config.get(CONF_UNIT_OF_MEASUREMENT):
            raise vol.Invalid(
                f"Specifying `{CONF_OPTIONS}` is not allowed together with "
                f"the `{CONF_STATE_CLASS}` or `{CONF_UNIT_OF_MEASUREMENT}` option"
            )

        if (device_class := config.get(CONF_DEVICE_CLASS)) != SensorDeviceClass.ENUM:
            raise vol.Invalid(
                f"The option `{CONF_OPTIONS}` must be used "
                f"together with device class `{SensorDeviceClass.ENUM}`, "
                f"got `{CONF_DEVICE_CLASS}` '{device_class}'"
            )

    if (
        (state_class := config.get(CONF_STATE_CLASS)) is not None
        and state_class in STATE_CLASS_UNITS
        and (unit_of_measurement := config.get(CONF_UNIT_OF_MEASUREMENT))
        not in STATE_CLASS_UNITS[state_class]
    ):
        raise vol.Invalid(
            f"The unit of measurement '{unit_of_measurement}' is not valid "
            f"together with state class '{state_class}'"
        )

    if (unit_of_measurement := config.get(CONF_UNIT_OF_MEASUREMENT)) is None:
        return config

    unit_of_measurement = config[CONF_UNIT_OF_MEASUREMENT] = AMBIGUOUS_UNITS.get(
        unit_of_measurement, unit_of_measurement
    )

    if (device_class := config.get(CONF_DEVICE_CLASS)) is None:
        return config

    if (
        device_class in DEVICE_CLASS_UNITS
        and unit_of_measurement not in DEVICE_CLASS_UNITS[device_class]
    ):
        raise vol.Invalid(
            f"The unit of measurement `{unit_of_measurement}` is not valid "
            f"together with device class `{device_class}`",
        )

    return config