def try_importing(label):
    """
    Try importing a test label, and return (is_importable, is_package).

    Relative labels like "." and ".." are seen as directories.
    """
    try:
        mod = import_module(label)
    except (ImportError, TypeError):
        return (False, False)

    return (True, hasattr(mod, "__path__"))