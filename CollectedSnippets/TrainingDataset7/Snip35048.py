def test_iter_test_cases_custom_test_suite_class(self):
        suite = self.make_test_suite(suite_class=MySuite)
        tests = iter_test_cases(suite)
        self.assertTestNames(
            tests,
            expected=[
                "Tests1.test1",
                "Tests1.test2",
                "Tests2.test1",
                "Tests2.test2",
            ],
        )