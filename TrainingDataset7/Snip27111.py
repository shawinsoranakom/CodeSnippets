def test_makemigrations_scriptable_merge(self, mock_input):
        out = io.StringIO()
        err = io.StringIO()
        with self.temporary_migration_module(
            module="migrations.test_migrations_conflict",
        ) as migration_dir:
            call_command(
                "makemigrations",
                "migrations",
                merge=True,
                name="merge",
                scriptable=True,
                stdout=out,
                stderr=err,
            )
        merge_file = os.path.join(migration_dir, "0003_merge.py")
        self.assertEqual(out.getvalue(), f"{merge_file}\n")
        self.assertIn(f"Created new merge migration {merge_file}", err.getvalue())