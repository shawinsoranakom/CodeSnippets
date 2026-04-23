def test_makemigrations_no_changes(self):
        """
        makemigrations exits when there are no changes to an app.
        """
        out = io.StringIO()
        with self.temporary_migration_module(
            module="migrations.test_migrations_no_changes"
        ):
            call_command("makemigrations", "migrations", stdout=out)
        self.assertIn("No changes detected in app 'migrations'", out.getvalue())