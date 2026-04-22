def is_pex():
    """Return if streamlit running in pex.

    Pex modifies sys.path so the pex file is the first path and that's
    how we determine we're running in the pex file.
    """
    if re.match(r".*pex$", sys.path[0]):
        return True
    return False