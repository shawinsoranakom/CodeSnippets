def _global_development_mode() -> bool:
    """Are we in development mode.

    This option defaults to True if and only if Streamlit wasn't installed
    normally.
    """
    return (
        not env_util.is_pex()
        and "site-packages" not in __file__
        and "dist-packages" not in __file__
        and "__pypackages__" not in __file__
    )