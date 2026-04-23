def _set_option(key: str, value: Any, where_defined: str) -> None:
    """Set a config option by key / value pair.

    This function assumes that the _config_options dictionary has already been
    populated and thus should only be used within this file and by tests.

    Parameters
    ----------
    key : str
        The key of the option, like "logger.level".
    value
        The value of the option.
    where_defined : str
        Tells the config system where this was set.

    """
    assert (
        _config_options is not None
    ), "_config_options should always be populated here."
    if key not in _config_options:
        # Import logger locally to prevent circular references
        from streamlit.logger import get_logger

        LOGGER = get_logger(__name__)

        LOGGER.warning(
            f'"{key}" is not a valid config option. If you previously had this config option set, it may have been removed.'
        )

    else:
        _config_options[key].set_value(value, where_defined)