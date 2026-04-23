def _convert_config_option_to_click_option(config_option):
    """Composes given config option options as options for click lib."""
    option = "--{}".format(config_option.key)
    param = config_option.key.replace(".", "_")
    description = config_option.description
    if config_option.deprecated:
        description += "\n {} - {}".format(
            config_option.deprecation_text, config_option.expiration_date
        )
    envvar = "STREAMLIT_{}".format(to_snake_case(param).upper())

    return {
        "param": param,
        "description": description,
        "type": config_option.type,
        "option": option,
        "envvar": envvar,
    }