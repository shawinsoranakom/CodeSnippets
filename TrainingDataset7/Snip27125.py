def test_makemigrations_migration_path_output_valueerror(self):
        """
        makemigrations prints the absolute path if os.path.relpath() raises a
        ValueError when it's impossible to obtain a relative path, e.g. on
        Windows if Django is installed on a different drive than where the
        migration files are created.
        """
        out = io.StringIO()
        with self.temporary_migration_module() as migration_dir:
            with mock.patch("os.path.relpath", side_effect=ValueError):
                call_command("makemigrations", "migrations", stdout=out)
        self.assertIn(os.path.join(migration_dir, "0001_initial.py"), out.getvalue())