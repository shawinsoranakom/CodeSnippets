def assertTestNames(self, tests, expected):
        # Each test.id() has a form like the following:
        # "test_runner.tests.IterTestCasesTests.test_iter_test_cases.<locals>.Tests1.test1".
        # It suffices to check only the last two parts.
        names = [".".join(test.id().split(".")[-2:]) for test in tests]
        self.assertEqual(names, expected)