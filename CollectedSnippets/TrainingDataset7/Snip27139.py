def test_makemigrations_update_squash_migration(self):
        with self.temporary_migration_module(
            module="migrations.test_migrations_squashed"
        ):
            msg = "Cannot update squash migration 'migrations.0001_squashed_0002'."
            with self.assertRaisesMessage(CommandError, msg):
                call_command("makemigrations", "migrations", update=True)