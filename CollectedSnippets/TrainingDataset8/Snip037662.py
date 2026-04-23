def get_streamlit_file_path(*filepath) -> str:
    """Return the full path to a file in ~/.streamlit.

    This doesn't guarantee that the file (or its directory) exists.
    """
    # os.path.expanduser works on OSX, Linux and Windows
    home = os.path.expanduser("~")
    if home is None:
        raise RuntimeError("No home directory.")

    return os.path.join(home, CONFIG_FOLDER_NAME, *filepath)