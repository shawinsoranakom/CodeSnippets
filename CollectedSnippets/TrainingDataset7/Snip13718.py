def shuffle_tests(tests, shuffler):
    """
    Return an iterator over the given tests in a shuffled order, keeping tests
    next to other tests of their class.

    `tests` should be an iterable of tests.
    """
    tests_by_type = {}
    for _, class_tests in itertools.groupby(tests, type):
        class_tests = list(class_tests)
        test_type = type(class_tests[0])
        class_tests = shuffler.shuffle(class_tests, key=lambda test: test.id())
        tests_by_type[test_type] = class_tests

    classes = shuffler.shuffle(tests_by_type, key=_class_shuffle_key)

    return itertools.chain(*(tests_by_type[cls] for cls in classes))