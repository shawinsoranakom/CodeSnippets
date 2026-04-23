def pytest_collection_modifyitems(config, items):
    pathfilter_file = config.getoption("--path-filter")
    if not pathfilter_file:
        return

    if not os.path.exists(pathfilter_file):
        raise ValueError(f"Pathfilter file does not exist: {pathfilter_file}")

    with open(pathfilter_file) as f:
        pathfilter_substrings = [line.strip() for line in f.readlines() if line.strip()]

        if not pathfilter_substrings:
            return  # No filtering if the list is empty => full test suite

        # this is technically redundant since we can just add "tests/" instead as a line item. still prefer to be explicit here
        if any(p == SENTINEL_ALL_TESTS for p in pathfilter_substrings):
            return  # at least one change should lead to a full run

        # technically doesn't even need to be checked since the loop below will take care of it
        if all(p == SENTINEL_NO_TEST for p in pathfilter_substrings):
            items[:] = []
            #  we only got sentinal values that signal a change that doesn't need to be tested, so delesect all
            config.hook.pytest_deselected(items=items)
            return

        # Filter tests based on the path substrings
        selected = []
        deselected = []
        for item in items:
            if any(substr in item.fspath.strpath for substr in pathfilter_substrings):
                selected.append(item)
            else:
                deselected.append(item)

        # Update list of test items to only those selected
        items[:] = selected
        config.hook.pytest_deselected(items=deselected)