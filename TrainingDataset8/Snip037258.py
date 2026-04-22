def set_user_option(key: str, value: Any) -> None:
    """Set config option.

    Currently, only the following config options can be set within the script itself:
        * client.caching
        * client.displayEnabled
        * deprecation.*

    Calling with any other options will raise StreamlitAPIException.

    Run `streamlit config show` in the terminal to see all available options.

    Parameters
    ----------
    key : str
        The config option key of the form "section.optionName". To see all
        available options, run `streamlit config show` on a terminal.

    value
        The new value to assign to this config option.

    """
    try:
        opt = _config_options_template[key]
    except KeyError as ke:
        raise StreamlitAPIException(
            "Unrecognized config option: {key}".format(key=key)
        ) from ke
    if opt.scriptable:
        set_option(key, value)
        return

    raise StreamlitAPIException(
        "{key} cannot be set on the fly. Set as command line option, e.g. streamlit run script.py --{key}, or in config.toml instead.".format(
            key=key
        )
    )