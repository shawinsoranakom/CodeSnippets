def test_makemigrations_update_manual_porting(self):
        with self.temporary_migration_module(
            module="migrations.test_migrations_plan"
        ) as migration_dir:
            with captured_stdout() as out:
                call_command("makemigrations", "migrations", update=True)
            # Previous migration exists.
            previous_migration_file = os.path.join(migration_dir, "0005_fifth.py")
            self.assertIs(os.path.exists(previous_migration_file), True)
            # New updated migration exists.
            files = [f for f in os.listdir(migration_dir) if f.startswith("0005_auto")]
            updated_migration_file = os.path.join(migration_dir, files[0])
            self.assertIs(os.path.exists(updated_migration_file), True)
            self.assertIn(
                f"Updated migration {updated_migration_file} requires manual porting.\n"
                f"Previous migration {previous_migration_file} was kept and must be "
                f"deleted after porting functions manually.",
                out.getvalue(),
            )