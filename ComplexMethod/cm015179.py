def pytest_collection_modifyitems(items: list[Any]) -> None:
    """
    This hook is used when rerunning disabled tests to get rid of all skipped tests
    instead of running and skipping them N times. This avoids flooding the console
    and XML outputs with junk. So we want this to run last when collecting tests.
    """
    rerun_disabled_tests = os.getenv("PYTORCH_TEST_RERUN_DISABLED_TESTS", "0") == "1"
    if not rerun_disabled_tests:
        return

    disabled_regex = re.compile(r"(?P<test_name>.+)\s+\([^\.]+\.(?P<test_class>.+)\)")
    disabled_tests = defaultdict(set)

    # This environment has already been set by run_test before it calls pytest
    disabled_tests_file = os.getenv("DISABLED_TESTS_FILE", "")
    if not disabled_tests_file or not os.path.exists(disabled_tests_file):
        return

    with open(disabled_tests_file) as fp:
        for disabled_test in json.load(fp):
            m = disabled_regex.match(disabled_test)
            if m:
                test_name = m["test_name"]
                test_class = m["test_class"]
                disabled_tests[test_class].add(test_name)

    # When rerunning disabled test, ignore all test cases that are not disabled
    filtered_items = []

    for item in items:
        test_name = item.name
        test_class = item.parent.name

        if (
            test_class not in disabled_tests
            or test_name not in disabled_tests[test_class]
        ):
            continue

        cpy = copy.copy(item)
        cpy._initrequest()

        filtered_items.append(cpy)

    items.clear()
    # NB: Need to edit items directly here to have the list reflected back to pytest
    items.extend(filtered_items)