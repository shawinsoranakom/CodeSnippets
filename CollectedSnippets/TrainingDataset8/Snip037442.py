def _is_in_streamlit_package(file: str) -> bool:
    """True if the given file is part of the streamlit package."""
    try:
        common_prefix = os.path.commonprefix([os.path.realpath(file), _STREAMLIT_DIR])
    except ValueError:
        # Raised if paths are on different drives.
        return False

    return common_prefix == _STREAMLIT_DIR