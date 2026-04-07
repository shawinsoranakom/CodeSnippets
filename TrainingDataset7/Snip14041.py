def clear_script_prefix():
    """
    Unset the script prefix for the current thread.
    """
    try:
        del _prefixes.value
    except AttributeError:
        pass