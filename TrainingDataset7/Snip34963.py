def test_tag_inheritance(self):
        def count_tests(**kwargs):
            kwargs.setdefault("verbosity", 0)
            suite = DiscoverRunner(**kwargs).build_suite(
                ["test_runner_apps.tagged.tests_inheritance"]
            )
            return suite.countTestCases()

        self.assertEqual(count_tests(tags=["foo"]), 4)
        self.assertEqual(count_tests(tags=["bar"]), 2)
        self.assertEqual(count_tests(tags=["baz"]), 2)
        self.assertEqual(count_tests(tags=["foo"], exclude_tags=["bar"]), 2)
        self.assertEqual(count_tests(tags=["foo"], exclude_tags=["bar", "baz"]), 1)
        self.assertEqual(count_tests(exclude_tags=["foo"]), 0)