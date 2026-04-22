def set_option(key: str, value: Any, where_defined: str = _USER_DEFINED) -> None:
    """Set config option.

    Run `streamlit config show` in the terminal to see all available options.

    This is an internal API. The public `st.set_option` API is implemented
    in `set_user_option`.

    Parameters
    ----------
    key : str
        The config option key of the form "section.optionName". To see all
        available options, run `streamlit config show` on a terminal.

    value
        The new value to assign to this config option.

    where_defined : str
        Tells the config system where this was set.
    """

    with _config_lock:
        # Ensure that our config files have been parsed.
        get_config_options()
        _set_option(key, value, where_defined)