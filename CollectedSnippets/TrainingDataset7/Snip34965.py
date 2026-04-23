def test_included_tags_displayed(self):
        runner = DiscoverRunner(tags=["foo", "bar"], verbosity=2)
        with captured_stdout() as stdout:
            runner.build_suite(["test_runner_apps.tagged.tests"])
            self.assertIn("Including test tag(s): bar, foo.\n", stdout.getvalue())