def reorder_tests(tests, classes, reverse=False, shuffler=None):
    """
    Reorder an iterable of tests, grouping by the given TestCase classes.

    This function also removes any duplicates and reorders so that tests of the
    same type are consecutive.

    The result is returned as an iterator. `classes` is a sequence of types.
    Tests that are instances of `classes[0]` are grouped first, followed by
    instances of `classes[1]`, etc. Tests that are not instances of any of the
    classes are grouped last.

    If `reverse` is True, the tests within each `classes` group are reversed,
    but without reversing the order of `classes` itself.

    The `shuffler` argument is an optional instance of this module's `Shuffler`
    class. If provided, tests will be shuffled within each `classes` group, but
    keeping tests with other tests of their TestCase class. Reversing is
    applied after shuffling to allow reversing the same random order.
    """
    # Each bin maps TestCase class to OrderedSet of tests. This permits tests
    # to be grouped by TestCase class even if provided non-consecutively.
    bins = [defaultdict(OrderedSet) for i in range(len(classes) + 1)]
    *class_bins, last_bin = bins

    for test in tests:
        for test_bin, test_class in zip(class_bins, classes):
            if isinstance(test, test_class):
                break
        else:
            test_bin = last_bin
        test_bin[type(test)].add(test)

    for test_bin in bins:
        # Call list() since reorder_test_bin()'s input must support reversed().
        tests = list(itertools.chain.from_iterable(test_bin.values()))
        yield from reorder_test_bin(tests, shuffler=shuffler, reverse=reverse)