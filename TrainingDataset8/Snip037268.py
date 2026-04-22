def _server_headless() -> bool:
    """If false, will attempt to open a browser window on start.

    Default: false unless (1) we are on a Linux box where DISPLAY is unset, or
    (2) we are running in the Streamlit Atom plugin.
    """
    if env_util.IS_LINUX_OR_BSD and not os.getenv("DISPLAY"):
        # We're running in Linux and DISPLAY is unset
        return True

    if os.getenv("IS_RUNNING_IN_STREAMLIT_EDITOR_PLUGIN") is not None:
        # We're running within the Streamlit Atom plugin
        return True

    return False