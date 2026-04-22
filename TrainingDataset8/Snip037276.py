def _update_config_with_toml(raw_toml: str, where_defined: str) -> None:
    """Update the config system by parsing this string.

    This should only be called from get_config_options.

    Parameters
    ----------
    raw_toml : str
        The TOML file to parse to update the config values.
    where_defined : str
        Tells the config system where this was set.

    """
    parsed_config_file = toml.loads(raw_toml)

    for section, options in parsed_config_file.items():
        for name, value in options.items():
            value = _maybe_read_env_variable(value)
            _set_option(f"{section}.{name}", value, where_defined)