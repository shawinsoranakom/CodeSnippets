def test_run_suite_logs_seed_exception(self):
        """
        run_suite() logs the seed when TestRunner.run() raises an exception.
        """

        class TestRunner:
            def run(self, suite):
                raise RuntimeError("my exception")

        result, output = self.run_suite_with_runner(TestRunner, shuffle=2)
        self.assertEqual(result, "my exception")
        expected_output = "Used shuffle seed: 2 (given)\n"
        self.assertEqual(output, expected_output)