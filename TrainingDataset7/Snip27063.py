def test_migrate_partially_applied_squashed_migration(self):
        """
        Migrating to a squashed migration specified by name should succeed
        even if it is partially applied.
        """
        with self.temporary_migration_module(module="migrations.test_migrations"):
            recorder = MigrationRecorder(connection)
            try:
                call_command("migrate", "migrations", "0001_initial", verbosity=0)
                call_command(
                    "squashmigrations",
                    "migrations",
                    "0002",
                    interactive=False,
                    verbosity=0,
                )
                call_command(
                    "migrate",
                    "migrations",
                    "0001_squashed_0002_second",
                    verbosity=0,
                )
                applied_migrations = recorder.applied_migrations()
                self.assertIn(("migrations", "0002_second"), applied_migrations)
            finally:
                # Unmigrate everything.
                call_command("migrate", "migrations", "zero", verbosity=0)