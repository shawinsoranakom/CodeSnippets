def test_makemigrations_update_existing_name(self):
        with self.temporary_migration_module(
            module="migrations.test_auto_now_add"
        ) as migration_dir:
            migration_file = os.path.join(migration_dir, "0001_initial.py")
            with open(migration_file) as fp:
                initial_content = fp.read()

            with captured_stdout() as out:
                call_command("makemigrations", "migrations", update=True)
            self.assertIs(os.path.exists(migration_file), False)
            new_migration_file = os.path.join(
                migration_dir,
                "0001_initial_updated.py",
            )
            with open(new_migration_file) as fp:
                self.assertNotEqual(initial_content, fp.read())
            self.assertIn(f"Deleted {migration_file}", out.getvalue())