def iter_test_cases(tests):
    """
    Return an iterator over a test suite's unittest.TestCase objects.

    The tests argument can also be an iterable of TestCase objects.
    """
    for test in tests:
        if isinstance(test, str):
            # Prevent an unfriendly RecursionError that can happen with
            # strings.
            raise TypeError(
                f"Test {test!r} must be a test case or test suite not string "
                f"(was found in {tests!r})."
            )
        if isinstance(test, TestCase):
            yield test
        else:
            # Otherwise, assume it is a test suite.
            yield from iter_test_cases(test)