def test_run_checks_passes_and_teardown_raises(self):
        """
        Exceptions on teardown are surfaced if no exceptions happen during
        run_checks().
        """
        with (
            mock.patch("django.test.runner.DiscoverRunner.setup_test_environment"),
            mock.patch("django.test.runner.DiscoverRunner.setup_databases"),
            mock.patch("django.test.runner.DiscoverRunner.build_suite"),
            mock.patch("django.test.runner.DiscoverRunner.run_checks"),
            mock.patch(
                "django.test.runner.DiscoverRunner.teardown_databases",
                side_effect=ValueError,
            ) as teardown_databases,
            mock.patch(
                "django.test.runner.DiscoverRunner.teardown_test_environment"
            ) as teardown_test_environment,
        ):
            runner = DiscoverRunner(verbosity=0, interactive=False)
            with self.assertRaises(ValueError):
                # Suppress the output when running TestDjangoTestCase.
                with mock.patch("sys.stderr"):
                    runner.run_tests(
                        ["test_runner_apps.sample.tests_sample.TestDjangoTestCase"]
                    )
            self.assertTrue(teardown_databases.called)
            self.assertFalse(teardown_test_environment.called)