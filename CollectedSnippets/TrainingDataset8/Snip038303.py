def _get_installed_streamlit_version() -> packaging.version.Version:
    """Return the streamlit version string from setup.py.

    Returns
    -------
    str
        The version string specified in setup.py.

    """
    return _version_str_to_obj(STREAMLIT_VERSION_STRING)