def test_number_of_tests_found_displayed(self):
        runner = DiscoverRunner()
        with captured_stdout() as stdout:
            runner.build_suite(
                [
                    "test_runner_apps.sample.tests_sample.TestDjangoTestCase",
                    "test_runner_apps.simple",
                ]
            )
            self.assertIn("Found 14 test(s).\n", stdout.getvalue())