def test_dotted_test_class_django_testcase(self):
        count = (
            DiscoverRunner(verbosity=0)
            .build_suite(
                ["test_runner_apps.sample.tests_sample.TestDjangoTestCase"],
            )
            .countTestCases()
        )

        self.assertEqual(count, 1)