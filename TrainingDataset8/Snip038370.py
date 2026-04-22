def load_config_options(flag_options: Dict[str, Any]) -> None:
    """Load config options from config.toml files, then overlay the ones set by
    flag_options.

    The "streamlit run" command supports passing Streamlit's config options
    as flags. This function reads through the config options set via flag,
    massages them, and passes them to get_config_options() so that they
    overwrite config option defaults and those loaded from config.toml files.

    Parameters
    ----------
    flag_options : Dict[str, Any]
        A dict of config options where the keys are the CLI flag version of the
        config option names.
    """
    options_from_flags = {
        name.replace("_", "."): val
        for name, val in flag_options.items()
        if val is not None
    }

    # Force a reparse of config files (if they exist). The result is cached
    # for future calls.
    config.get_config_options(force_reparse=True, options_from_flags=options_from_flags)