def test_failure_to_format_code(self):
        self.assertFormatterFailureCaught(
            "squashmigrations", "migrations", "0002", interactive=False
        )