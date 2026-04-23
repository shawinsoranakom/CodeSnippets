def test_tag_fail_to_load(self):
        with self.assertRaises(SyntaxError):
            import_module("test_runner_apps.tagged.tests_syntax_error")
        runner = DiscoverRunner(tags=["syntax_error"], verbosity=0)
        # A label that doesn't exist or cannot be loaded due to syntax errors
        # is always considered matching.
        suite = runner.build_suite(["doesnotexist", "test_runner_apps.tagged"])
        self.assertEqual(
            [test.id() for test in suite],
            [
                "unittest.loader._FailedTest.doesnotexist",
                "unittest.loader._FailedTest.test_runner_apps.tagged."
                "tests_syntax_error",
            ],
        )