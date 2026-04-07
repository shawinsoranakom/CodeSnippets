def test_makemigrations_migrations_announce(self):
        """
        makemigrations announces the migration at the default verbosity level.
        """
        out = io.StringIO()
        with self.temporary_migration_module():
            call_command("makemigrations", "migrations", stdout=out)
        self.assertIn("Migrations for 'migrations'", out.getvalue())