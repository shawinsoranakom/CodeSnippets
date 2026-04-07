def test_squashmigrations_invalid_start(self):
        """
        squashmigrations doesn't accept a starting migration after the ending
        migration.
        """
        with self.temporary_migration_module(
            module="migrations.test_migrations_no_changes"
        ):
            msg = (
                "The migration 'migrations.0003_third' cannot be found. Maybe "
                "it comes after the migration 'migrations.0002_second'"
            )
            with self.assertRaisesMessage(CommandError, msg):
                call_command(
                    "squashmigrations",
                    "migrations",
                    "0003",
                    "0002",
                    interactive=False,
                    verbosity=0,
                )