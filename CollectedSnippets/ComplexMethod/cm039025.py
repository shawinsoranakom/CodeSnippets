def pytest_collection_modifyitems(config, items):
    """Called after collect is completed.

    Parameters
    ----------
    config : pytest config
    items : list of collected items
    """
    skip_doctests = False
    if np_base_version < parse_version("2"):
        # TODO: configure numpy to output scalar arrays as regular Python scalars
        # once possible to improve readability of the tests docstrings.
        # https://numpy.org/neps/nep-0051-scalar-representation.html#implementation
        reason = "Due to NEP 51 numpy scalar repr has changed in numpy 2"
        skip_doctests = True

    if sp_version < parse_version("1.14"):
        reason = "Scipy sparse matrix repr has changed in scipy 1.14"
        skip_doctests = True

    # Normally doctest has the entire module's scope. Here we set globs to an empty dict
    # to remove the module's scope:
    # https://docs.python.org/3/library/doctest.html#what-s-the-execution-context
    for item in items:
        if isinstance(item, DoctestItem):
            item.dtest.globs = {}

    if skip_doctests:
        skip_marker = pytest.mark.skip(reason=reason)

        for item in items:
            if isinstance(item, DoctestItem):
                item.add_marker(skip_marker)