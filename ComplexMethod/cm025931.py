def validate_sensor_attributes(
    dpt_info: DPTInfo, config: dict[str, Any]
) -> dict[str, Any]:
    """Validate that state_class is compatible with device_class and unit_of_measurement.

    Works for both, UI and YAML configuration schema since they
    share same names for all tested attributes.
    """
    state_class = config.get(
        CONF_SENSOR_STATE_CLASS,
        dpt_info["sensor_state_class"],
    )
    device_class = config.get(
        CONF_DEVICE_CLASS,
        dpt_info["sensor_device_class"],
    )
    unit_of_measurement = config.get(
        CONF_UNIT_OF_MEASUREMENT,
        dpt_info["unit"],
    )
    if (
        state_class
        and device_class
        and (state_classes := DEVICE_CLASS_STATE_CLASSES.get(device_class)) is not None
        and state_class not in state_classes
    ):
        raise vol.Invalid(
            f"State class '{state_class}' is not valid for device class '{device_class}'. "
            f"Valid options are: {', '.join(sorted(map(str, state_classes), key=str.casefold))}",
            path=[CONF_SENSOR_STATE_CLASS],
        )
    if (
        device_class
        and (d_c_units := DEVICE_CLASS_UNITS.get(device_class)) is not None
        and unit_of_measurement not in d_c_units
    ):
        raise vol.Invalid(
            f"Unit of measurement '{unit_of_measurement}' is not valid for device class '{device_class}'. "
            f"Valid options are: {', '.join(sorted(map(str, d_c_units), key=str.casefold))}",
            path=(
                [CONF_DEVICE_CLASS]
                if CONF_DEVICE_CLASS in config
                else [CONF_UNIT_OF_MEASUREMENT]
            ),
        )
    if (
        state_class
        and (s_c_units := STATE_CLASS_UNITS.get(state_class)) is not None
        and unit_of_measurement not in s_c_units
    ):
        raise vol.Invalid(
            f"Unit of measurement '{unit_of_measurement}' is not valid for state class '{state_class}'. "
            f"Valid options are: {', '.join(sorted(map(str, s_c_units), key=str.casefold))}",
            path=(
                [CONF_SENSOR_STATE_CLASS]
                if CONF_SENSOR_STATE_CLASS in config
                else [CONF_UNIT_OF_MEASUREMENT]
            ),
        )
    return config