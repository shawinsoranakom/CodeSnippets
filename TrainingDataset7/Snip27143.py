def test_squashmigrations_replacement_cycle(self):
        out = io.StringIO()
        with self.temporary_migration_module(
            module="migrations.test_migrations_squashed_loop"
        ):
            # Hits a squash replacement cycle check error, but the actual
            # failure is dependent on the order in which the files are read on
            # disk.
            with self.assertRaisesRegex(
                CommandError,
                r"Cyclical squash replacement found, starting at"
                r" \('migrations', '2_(squashed|auto)'\)",
            ):
                call_command(
                    "migrate", "migrations", "--plan", interactive=False, stdout=out
                )