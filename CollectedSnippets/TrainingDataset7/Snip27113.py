def test_merge_makemigrations_failure_to_format_code(self):
        self.assertFormatterFailureCaught("makemigrations", "migrations", empty=True)
        self.assertFormatterFailureCaught(
            "makemigrations",
            "migrations",
            merge=True,
            interactive=False,
            module="migrations.test_migrations_conflict",
        )