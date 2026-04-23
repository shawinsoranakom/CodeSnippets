def partition_suite_by_case(suite):
    """Partition a test suite by TestCase, preserving the order of tests."""
    suite_class = type(suite)
    all_tests = iter_test_cases(suite)
    return [suite_class(tests) for _, tests in itertools.groupby(all_tests, type)]