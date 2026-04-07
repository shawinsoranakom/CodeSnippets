def filter_tests_by_tags(tests, tags, exclude_tags):
    """Return the matching tests as an iterator."""
    return (test for test in tests if test_match_tags(test, tags, exclude_tags))