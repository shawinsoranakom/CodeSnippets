def test_makemigrations_scriptable(self):
        """
        With scriptable=True, log output is diverted to stderr, and only the
        paths of generated migration files are written to stdout.
        """
        out = io.StringIO()
        err = io.StringIO()
        with self.temporary_migration_module(
            module="migrations.migrations.test_migrations",
        ) as migration_dir:
            call_command(
                "makemigrations",
                "migrations",
                scriptable=True,
                stdout=out,
                stderr=err,
            )
        initial_file = os.path.join(migration_dir, "0001_initial.py")
        self.assertEqual(out.getvalue(), f"{initial_file}\n")
        self.assertIn("    + Create model ModelWithCustomBase\n", err.getvalue())