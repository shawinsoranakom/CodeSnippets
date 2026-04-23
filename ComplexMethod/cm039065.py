def pytest_collection_modifyitems(config, items):
    """Called after collect is completed.

    Parameters
    ----------
    config : pytest config
    items : list of collected items
    """
    run_network_tests = environ.get("SKLEARN_SKIP_NETWORK_TESTS", "1") == "0"
    skip_network = pytest.mark.skip(
        reason="test is enabled when SKLEARN_SKIP_NETWORK_TESTS=0"
    )

    # download datasets during collection to avoid thread unsafe behavior
    # when running pytest in parallel with pytest-xdist
    dataset_features_set = set(dataset_fetchers)
    datasets_to_download = set()

    for item in items:
        if isinstance(item, DoctestItem) and "fetch_" in item.name:
            fetcher_function_name = item.name.split(".")[-1]
            dataset_fetchers_key = f"{fetcher_function_name}_fxt"
            dataset_to_fetch = set([dataset_fetchers_key]) & dataset_features_set
        elif not hasattr(item, "fixturenames"):
            continue
        else:
            item_fixtures = set(item.fixturenames)
            dataset_to_fetch = item_fixtures & dataset_features_set

        if not dataset_to_fetch:
            continue

        if run_network_tests:
            datasets_to_download |= dataset_to_fetch
        else:
            # network tests are skipped
            item.add_marker(skip_network)

    # Only download datasets on the first worker spawned by pytest-xdist
    # to avoid thread unsafe behavior. If pytest-xdist is not used, we still
    # download before tests run.
    worker_id = environ.get("PYTEST_XDIST_WORKER", "gw0")
    if worker_id == "gw0" and run_network_tests:
        for name in datasets_to_download:
            with suppress(SkipTest):
                dataset_fetchers[name]()

    for item in items:
        # Known failure on with GradientBoostingClassifier on ARM64
        if (
            item.name.endswith("GradientBoostingClassifier")
            and platform.machine() == "aarch64"
        ):
            marker = pytest.mark.xfail(
                reason=(
                    "know failure. See "
                    "https://github.com/scikit-learn/scikit-learn/issues/17797"
                )
            )
            item.add_marker(marker)

    skip_doctests = False
    try:
        import matplotlib  # noqa: F401
    except ImportError:
        skip_doctests = True
        reason = "matplotlib is required to run the doctests"

    if _IS_32BIT:
        reason = "doctest are only run when the default numpy int is 64 bits."
        skip_doctests = True
    elif sys.platform.startswith("win32"):
        reason = (
            "doctests are not run for Windows because numpy arrays "
            "repr is inconsistent across platforms."
        )
        skip_doctests = True

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
                # work-around an internal error with pytest if adding a skip
                # mark to a doctest in a contextmanager, see
                # https://github.com/pytest-dev/pytest/issues/8796 for more
                # details.
                if item.name != "sklearn._config.config_context":
                    item.add_marker(skip_marker)
    try:
        import PIL  # noqa: F401

        pillow_installed = True
    except ImportError:
        pillow_installed = False

    if not pillow_installed:
        skip_marker = pytest.mark.skip(reason="pillow (or PIL) not installed!")
        for item in items:
            if item.name in [
                "sklearn.feature_extraction.image.PatchExtractor",
                "sklearn.feature_extraction.image.extract_patches_2d",
            ]:
                item.add_marker(skip_marker)