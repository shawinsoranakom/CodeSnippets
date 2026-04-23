def test_dotted_test_method_django_testcase(self):
        count = (
            DiscoverRunner(verbosity=0)
            .build_suite(
                ["test_runner_apps.sample.tests_sample.TestDjangoTestCase.test_sample"],
            )
            .countTestCases()
        )

        self.assertEqual(count, 1)