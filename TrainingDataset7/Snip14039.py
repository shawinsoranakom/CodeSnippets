def set_script_prefix(prefix):
    """
    Set the script prefix for the current thread.
    """
    if not prefix.endswith("/"):
        prefix += "/"
    _prefixes.value = prefix