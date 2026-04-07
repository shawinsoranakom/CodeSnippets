def test_makemigrations_migration_path_output(self):
        """
        makemigrations should print the relative paths to the migrations unless
        they are outside of the current tree, in which case the absolute path
        should be shown.
        """
        out = io.StringIO()
        apps.register_model("migrations", UnicodeModel)
        with self.temporary_migration_module() as migration_dir:
            call_command("makemigrations", "migrations", stdout=out)
            self.assertIn(
                os.path.join(migration_dir, "0001_initial.py"), out.getvalue()
            )