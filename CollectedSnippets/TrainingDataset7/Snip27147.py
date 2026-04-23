def test_double_replaced_migrations_are_checked_correctly(self):
        """
        If replaced migrations are already applied and replacing migrations
        are not, then migrate should not fail with
        InconsistentMigrationHistory.
        """
        with self.temporary_migration_module():
            call_command(
                "makemigrations",
                "migrations",
                "--empty",
                interactive=False,
                verbosity=0,
            )
            call_command(
                "makemigrations",
                "migrations",
                "--empty",
                interactive=False,
                verbosity=0,
            )
            call_command(
                "makemigrations",
                "migrations",
                "--empty",
                interactive=False,
                verbosity=0,
            )
            call_command(
                "makemigrations",
                "migrations",
                "--empty",
                interactive=False,
                verbosity=0,
            )
            call_command("migrate", "migrations", interactive=False, verbosity=0)
            call_command(
                "squashmigrations",
                "migrations",
                "0001",
                "0002",
                interactive=False,
                verbosity=0,
            )
            call_command(
                "squashmigrations",
                "migrations",
                "0001_initial_squashed",
                "0003",
                interactive=False,
                verbosity=0,
            )
            call_command("migrate", "migrations", interactive=False, verbosity=0)