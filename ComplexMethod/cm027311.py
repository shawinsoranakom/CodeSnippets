def validate_options(config: ConfigType) -> ConfigType:
    """Validate options.

    If set position topic is set then get position topic is set as well.
    """
    if CONF_SET_POSITION_TOPIC in config and CONF_GET_POSITION_TOPIC not in config:
        raise vol.Invalid(
            f"'{CONF_SET_POSITION_TOPIC}' must be set together with"
            f" '{CONF_GET_POSITION_TOPIC}'."
        )

    # if templates are set make sure the topic for the template is also set

    if CONF_VALUE_TEMPLATE in config and CONF_STATE_TOPIC not in config:
        raise vol.Invalid(
            f"'{CONF_VALUE_TEMPLATE}' must be set together with '{CONF_STATE_TOPIC}'."
        )

    if CONF_GET_POSITION_TEMPLATE in config and CONF_GET_POSITION_TOPIC not in config:
        raise vol.Invalid(
            f"'{CONF_GET_POSITION_TEMPLATE}' must be set together with"
            f" '{CONF_GET_POSITION_TOPIC}'."
        )

    if CONF_SET_POSITION_TEMPLATE in config and CONF_SET_POSITION_TOPIC not in config:
        raise vol.Invalid(
            f"'{CONF_SET_POSITION_TEMPLATE}' must be set together with"
            f" '{CONF_SET_POSITION_TOPIC}'."
        )

    if CONF_TILT_COMMAND_TEMPLATE in config and CONF_TILT_COMMAND_TOPIC not in config:
        raise vol.Invalid(
            f"'{CONF_TILT_COMMAND_TEMPLATE}' must be set together with"
            f" '{CONF_TILT_COMMAND_TOPIC}'."
        )

    if CONF_TILT_STATUS_TEMPLATE in config and CONF_TILT_STATUS_TOPIC not in config:
        raise vol.Invalid(
            f"'{CONF_TILT_STATUS_TEMPLATE}' must be set together with"
            f" '{CONF_TILT_STATUS_TOPIC}'."
        )

    return config