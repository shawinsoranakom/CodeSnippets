def show_config() -> None:
    """Print all config options to the terminal."""
    with _config_lock:
        config_util.show_config(
            _section_descriptions, cast(Dict[str, ConfigOption], _config_options)
        )