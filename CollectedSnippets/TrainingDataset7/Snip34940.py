def test_dotted_test_class_vanilla_unittest(self):
        count = (
            DiscoverRunner(verbosity=0)
            .build_suite(
                ["test_runner_apps.sample.tests_sample.TestVanillaUnittest"],
            )
            .countTestCases()
        )

        self.assertEqual(count, 1)