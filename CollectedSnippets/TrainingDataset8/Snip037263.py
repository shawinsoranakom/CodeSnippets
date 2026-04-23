def _delete_option(key: str) -> None:
    """Remove a ConfigOption by key from the global store.

    Only for use in testing.
    """
    try:
        del _config_options_template[key]
        del cast(Dict[str, ConfigOption], _config_options)[key]
    except Exception:
        # We don't care if the option already doesn't exist.
        pass