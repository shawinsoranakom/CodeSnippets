def test_excluded_tags_displayed(self):
        runner = DiscoverRunner(exclude_tags=["foo", "bar"], verbosity=3)
        with captured_stdout() as stdout:
            runner.build_suite(["test_runner_apps.tagged.tests"])
            self.assertIn("Excluding test tag(s): bar, foo.\n", stdout.getvalue())