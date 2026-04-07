def test_makemigrations_update_applied_migration(self):
        recorder = MigrationRecorder(connection)
        recorder.record_applied("migrations", "0001_initial")
        recorder.record_applied("migrations", "0002_second")
        with self.temporary_migration_module(module="migrations.test_migrations"):
            msg = "Cannot update applied migration 'migrations.0002_second'."
            with self.assertRaisesMessage(CommandError, msg):
                call_command("makemigrations", "migrations", update=True)