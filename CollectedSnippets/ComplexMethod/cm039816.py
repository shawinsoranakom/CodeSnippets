def all_displays():
    """Get a list of all displays from `sklearn`.

    Returns
    -------
    displays : list of tuples
        List of (name, class), where ``name`` is the display class name as
        string and ``class`` is the actual type of the class.

    Examples
    --------
    >>> from sklearn.utils.discovery import all_displays
    >>> displays = all_displays()
    >>> displays[0]
    ('CalibrationDisplay', <class 'sklearn.calibration.CalibrationDisplay'>)
    """
    # lazy import to avoid circular imports from sklearn.base
    from sklearn.utils._testing import ignore_warnings

    all_classes = []
    root = str(Path(__file__).parent.parent)  # sklearn package
    # Ignore deprecation warnings triggered at import time and from walking
    # packages
    with ignore_warnings(category=FutureWarning):
        for _, module_name, _ in pkgutil.walk_packages(path=[root], prefix="sklearn."):
            module_parts = module_name.split(".")
            if (
                any(part in _MODULE_TO_IGNORE for part in module_parts)
                or "._" in module_name
            ):
                continue
            module = import_module(module_name)
            classes = inspect.getmembers(module, inspect.isclass)
            classes = [
                (name, display_class)
                for name, display_class in classes
                if not name.startswith("_") and name.endswith("Display")
            ]
            all_classes.extend(classes)

    return sorted(set(all_classes), key=itemgetter(0))