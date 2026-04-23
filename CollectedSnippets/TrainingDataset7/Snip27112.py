def test_makemigrations_failure_to_format_code(self):
        self.assertFormatterFailureCaught("makemigrations", "migrations")