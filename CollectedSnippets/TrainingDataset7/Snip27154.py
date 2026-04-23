def test_squashed_name_without_start_migration_name(self):
        """--squashed-name also works if a start migration is omitted."""
        squashed_name = "squashed_name"
        with self.temporary_migration_module(
            module="migrations.test_migrations"
        ) as migration_dir:
            call_command(
                "squashmigrations",
                "migrations",
                "0001",
                squashed_name=squashed_name,
                interactive=False,
                verbosity=0,
            )
            squashed_migration_file = os.path.join(
                migration_dir, "0001_%s.py" % squashed_name
            )
            self.assertTrue(os.path.exists(squashed_migration_file))