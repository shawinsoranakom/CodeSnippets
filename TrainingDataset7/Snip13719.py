def reorder_test_bin(tests, shuffler=None, reverse=False):
    """
    Return an iterator that reorders the given tests, keeping tests next to
    other tests of their class.

    `tests` should be an iterable of tests that supports reversed().
    """
    if shuffler is None:
        if reverse:
            return reversed(tests)
        # The function must return an iterator.
        return iter(tests)

    tests = shuffle_tests(tests, shuffler)
    if not reverse:
        return tests
    # Arguments to reversed() must be reversible.
    return reversed(list(tests))