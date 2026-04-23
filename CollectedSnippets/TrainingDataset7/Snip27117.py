def test_makemigrations_unspecified_app_with_conflict_no_merge(self):
        """
        makemigrations does not raise a CommandError when an unspecified app
        has conflicting migrations.
        """
        with self.temporary_migration_module(
            module="migrations.test_migrations_no_changes"
        ):
            call_command("makemigrations", "migrations", merge=False, verbosity=0)