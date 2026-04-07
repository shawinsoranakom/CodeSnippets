def test_makemigrations_check_no_changes(self):
        """
        makemigrations --check should exit with a zero status when there are no
        changes.
        """
        out = io.StringIO()
        with self.temporary_migration_module(
            module="migrations.test_migrations_no_changes"
        ):
            call_command("makemigrations", "--check", "migrations", stdout=out)
        self.assertEqual("No changes detected in app 'migrations'\n", out.getvalue())