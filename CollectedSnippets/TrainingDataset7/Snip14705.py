def deactivate():
    """
    Uninstall the active translation object so that further _() calls resolve
    to the default translation object.
    """
    if hasattr(_active, "value"):
        del _active.value