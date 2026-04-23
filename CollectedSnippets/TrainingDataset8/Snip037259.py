def get_option(key: str) -> Any:
    """Return the current value of a given Streamlit config option.

    Run `streamlit config show` in the terminal to see all available options.

    Parameters
    ----------
    key : str
        The config option key of the form "section.optionName". To see all
        available options, run `streamlit config show` on a terminal.
    """
    with _config_lock:
        config_options = get_config_options()

        if key not in config_options:
            raise RuntimeError('Config key "%s" not defined.' % key)
        return config_options[key].value