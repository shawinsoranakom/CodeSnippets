def test_failure_to_format_code(self):
        self.assertFormatterFailureCaught("optimizemigration", "migrations", "0001")