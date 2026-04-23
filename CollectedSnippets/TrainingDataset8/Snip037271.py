def get_where_defined(key: str) -> str:
    """Indicate where (e.g. in which file) this option was defined.

    Parameters
    ----------
    key : str
        The config option key of the form "section.optionName"

    """
    with _config_lock:
        config_options = get_config_options()

        if key not in config_options:
            raise RuntimeError('Config key "%s" not defined.' % key)
        return config_options[key].where_defined