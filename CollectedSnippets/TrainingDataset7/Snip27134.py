def test_makemigrations_update(self):
        with self.temporary_migration_module(
            module="migrations.test_migrations"
        ) as migration_dir:
            migration_file = os.path.join(migration_dir, "0002_second.py")
            with open(migration_file) as fp:
                initial_content = fp.read()

            with captured_stdout() as out:
                call_command("makemigrations", "migrations", update=True)
            self.assertFalse(
                any(
                    filename.startswith("0003")
                    for filename in os.listdir(migration_dir)
                )
            )
            self.assertIs(os.path.exists(migration_file), False)
            new_migration_file = os.path.join(
                migration_dir,
                "0002_delete_tribble_author_rating_modelwithcustombase_and_more.py",
            )
            with open(new_migration_file) as fp:
                self.assertNotEqual(initial_content, fp.read())
            self.assertIn(f"Deleted {migration_file}", out.getvalue())