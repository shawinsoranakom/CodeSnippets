def test_squashed_name_exists(self):
        msg = "Migration 0001_initial already exists. Use a different name."
        with self.temporary_migration_module(module="migrations.test_migrations"):
            with self.assertRaisesMessage(CommandError, msg):
                call_command(
                    "squashmigrations",
                    "migrations",
                    "0001",
                    "0002",
                    squashed_name="initial",
                    interactive=False,
                    verbosity=0,
                )