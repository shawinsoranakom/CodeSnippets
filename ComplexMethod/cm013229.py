def lint_test_case_extension(suite):
    succeed = True
    for test_case_or_suite in suite:
        test_case = test_case_or_suite
        if isinstance(test_case_or_suite, unittest.TestSuite):
            first_test = test_case_or_suite._tests[0] if len(test_case_or_suite._tests) > 0 else None
            if first_test is not None and isinstance(first_test, unittest.TestSuite):
                return succeed and lint_test_case_extension(test_case_or_suite)
            test_case = first_test

        if test_case is not None:
            if not isinstance(test_case, TestCase):
                test_class = test_case.id().split('.', 1)[1].split('.')[0]
                err = "This test class should extend from torch.testing._internal.common_utils.TestCase but it doesn't."
                print(f"{test_class} - failed. {err}")
                succeed = False
    return succeed