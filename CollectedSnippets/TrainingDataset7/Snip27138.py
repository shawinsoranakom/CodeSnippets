def test_makemigrations_update_no_migration(self):
        with self.temporary_migration_module(module="migrations.test_migrations_empty"):
            msg = "App migrations has no migration, cannot update last migration."
            with self.assertRaisesMessage(CommandError, msg):
                call_command("makemigrations", "migrations", update=True)