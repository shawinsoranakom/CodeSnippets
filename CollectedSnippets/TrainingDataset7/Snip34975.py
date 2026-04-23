def test_run_suite_logs_seed(self):
        class TestRunner:
            def run(self, suite):
                return "<fake-result>"

        expected_prefix = "Used shuffle seed"
        # Test with and without shuffling enabled.
        result, output = self.run_suite_with_runner(TestRunner)
        self.assertEqual(result, "<fake-result>")
        self.assertNotIn(expected_prefix, output)

        result, output = self.run_suite_with_runner(TestRunner, shuffle=2)
        self.assertEqual(result, "<fake-result>")
        expected_output = f"{expected_prefix}: 2 (given)\n"
        self.assertEqual(output, expected_output)