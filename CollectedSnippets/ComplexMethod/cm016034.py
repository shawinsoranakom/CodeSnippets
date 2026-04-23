def compute_pass_rate(eager_dir, dynamo_dir):
    print("parsing xmls")
    eager_xmls = open_test_results(eager_dir)
    dynamo_xmls = open_test_results(dynamo_dir)

    print("computing pass rate")
    eager_passed = get_passed_testcases(eager_xmls)
    dynamo_passed = get_passed_testcases(dynamo_xmls)
    dynamo_pass_keys = {key(testcase) for testcase in dynamo_passed}
    dynamo_pass_keys = {key_ for key_ in dynamo_pass_keys if not should_exclude(key_)}
    tmp_eager_pass_keys = {key(testcase) for testcase in eager_passed}
    tmp_eager_pass_keys = {
        key_ for key_ in tmp_eager_pass_keys if not should_exclude(key_)
    }
    excluded = [key(t) for t in get_excluded_testcases(dynamo_xmls)]
    eager_pass_keys = tmp_eager_pass_keys - set(excluded)

    subset = eager_pass_keys.intersection(dynamo_pass_keys)
    total_subset = len(subset)
    total_tests = len(eager_pass_keys)
    print("pass rate", total_subset / total_tests, total_subset, total_tests)

    dynamo_testcases = get_testcases(dynamo_xmls)
    tc = {key(t): t for t in dynamo_testcases}

    # Useful for debugging
    not_there_keys = set()
    for key_ in eager_pass_keys:
        if key_ not in tc:
            not_there_keys.add(key_)

    fail_keys = eager_pass_keys - subset
    return fail_keys