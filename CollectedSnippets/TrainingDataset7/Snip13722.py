def test_match_tags(test, tags, exclude_tags):
    if isinstance(test, unittest.loader._FailedTest):
        # Tests that couldn't load always match to prevent tests from falsely
        # passing due e.g. to syntax errors.
        return True
    test_tags = set(getattr(test, "tags", []))
    test_fn_name = getattr(test, "_testMethodName", str(test))
    if hasattr(test, test_fn_name):
        test_fn = getattr(test, test_fn_name)
        test_fn_tags = list(getattr(test_fn, "tags", []))
        test_tags = test_tags.union(test_fn_tags)
    if tags and test_tags.isdisjoint(tags):
        return False
    return test_tags.isdisjoint(exclude_tags)