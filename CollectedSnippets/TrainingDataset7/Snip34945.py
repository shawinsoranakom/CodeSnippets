def test_loader_patterns_not_mutated(self):
        runner = DiscoverRunner(test_name_patterns=["test_sample"], verbosity=0)
        tests = [
            ("test_runner_apps.sample.tests", 1),
            ("test_runner_apps.sample.tests.Test.test_sample", 1),
            ("test_runner_apps.sample.empty", 0),
            ("test_runner_apps.sample.tests_sample.EmptyTestCase", 0),
        ]
        for test_labels, tests_count in tests:
            with self.subTest(test_labels=test_labels):
                with change_loader_patterns(["UnittestCase1"]):
                    count = runner.build_suite([test_labels]).countTestCases()
                    self.assertEqual(count, tests_count)
                    self.assertEqual(
                        runner.test_loader.testNamePatterns, ["UnittestCase1"]
                    )