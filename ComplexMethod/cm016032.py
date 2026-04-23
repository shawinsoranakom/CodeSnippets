def failures_histogram(eager_dir, dynamo_dir, verbose=False, format_issues=False):
    fail_keys = compute_pass_rate(eager_dir, dynamo_dir)
    xmls = open_test_results(dynamo_dir)

    testcases = get_testcases(xmls)
    testcases = [t for t in testcases if key(t) in fail_keys]
    dct = get_failures(testcases)

    result = []
    for count, reason, testcases in dct:
        if verbose:
            row = (
                count,
                reason,
                repro(testcases[0]),
                [all_tests(t) for t in testcases],
            )
        else:
            row = (count, reason, repro(testcases[0]))
        result.append(row)

    header = (
        "(num_failed_tests, error_msg, sample_test, all_tests)"
        if verbose
        else "(num_failed_tests, error_msg, sample_test)"
    )
    print(header)
    sum_counts = sum(r[0] for r in result)
    for row in result:
        if format_issues:
            print(as_issue(*row))
        else:
            print(row)
    print("[counts]", sum_counts)