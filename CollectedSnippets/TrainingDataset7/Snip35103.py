def test_run_checks_raises(self):
        """
        Teardown functions are run when run_checks() raises SystemCheckError.
        """
        with (
            mock.patch("django.test.runner.DiscoverRunner.setup_test_environment"),
            mock.patch("django.test.runner.DiscoverRunner.setup_databases"),
            mock.patch("django.test.runner.DiscoverRunner.build_suite"),
            mock.patch(
                "django.test.runner.DiscoverRunner.run_checks",
                side_effect=SystemCheckError,
            ),
            mock.patch(
                "django.test.runner.DiscoverRunner.teardown_databases"
            ) as teardown_databases,
            mock.patch(
                "django.test.runner.DiscoverRunner.teardown_test_environment"
            ) as teardown_test_environment,
        ):
            runner = DiscoverRunner(verbosity=0, interactive=False)
            with self.assertRaises(SystemCheckError):
                runner.run_tests(
                    ["test_runner_apps.sample.tests_sample.TestDjangoTestCase"]
                )
            self.assertTrue(teardown_databases.called)
            self.assertTrue(teardown_test_environment.called)