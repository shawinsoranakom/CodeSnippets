def test_squashmigrations_initial_attribute(self):
        with self.temporary_migration_module(
            module="migrations.test_migrations"
        ) as migration_dir:
            call_command(
                "squashmigrations", "migrations", "0002", interactive=False, verbosity=0
            )

            squashed_migration_file = os.path.join(
                migration_dir, "0001_squashed_0002_second.py"
            )
            with open(squashed_migration_file, encoding="utf-8") as fp:
                content = fp.read()
                self.assertIn("initial = True", content)