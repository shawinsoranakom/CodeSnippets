def validate_number_attributes(
    transcoder: type[DPTNumeric], config: dict[str, Any]
) -> dict[str, Any]:
    """Validate a number entity configurations dependent on configured value type.

    Works for both, UI and YAML configuration schema since they
    share same names for all tested attributes.
    """
    min_config: float | None = config.get(NumberConf.MIN)
    max_config: float | None = config.get(NumberConf.MAX)
    step_config: float | None = config.get(NumberConf.STEP)
    _dpt_error_str = f"DPT {transcoder.dpt_number_str()} '{transcoder.value_type}'"

    # Infinity is not supported by Home Assistant frontend so user defined
    # config is required if xknx DPTNumeric subclass defines it as limit.
    if min_config is None and transcoder.value_min == -math.inf:
        raise vol.Invalid(
            f"'min' key required for {_dpt_error_str}",
            path=[NumberConf.MIN],
        )
    if min_config is not None and min_config < transcoder.value_min:
        raise vol.Invalid(
            f"'min: {min_config}' undercuts possible minimum"
            f" of {_dpt_error_str}: {transcoder.value_min}",
            path=[NumberConf.MIN],
        )
    if max_config is None and transcoder.value_max == math.inf:
        raise vol.Invalid(
            f"'max' key required for {_dpt_error_str}",
            path=[NumberConf.MAX],
        )
    if max_config is not None and max_config > transcoder.value_max:
        raise vol.Invalid(
            f"'max: {max_config}' exceeds possible maximum"
            f" of {_dpt_error_str}: {transcoder.value_max}",
            path=[NumberConf.MAX],
        )
    if step_config is not None and step_config < transcoder.resolution:
        raise vol.Invalid(
            f"'step: {step_config}' undercuts possible minimum step"
            f" of {_dpt_error_str}: {transcoder.resolution}",
            path=[NumberConf.STEP],
        )

    # Validate device class and unit of measurement compatibility
    dpt_metadata = get_supported_dpts()[transcoder.dpt_number_str()]

    device_class = config.get(
        CONF_DEVICE_CLASS,
        dpt_metadata["sensor_device_class"],
    )
    unit_of_measurement = config.get(
        CONF_UNIT_OF_MEASUREMENT,
        dpt_metadata["unit"],
    )
    if (
        device_class
        and (d_c_units := NUMBER_DEVICE_CLASS_UNITS.get(device_class)) is not None
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

    return config