def test_makemigrations_empty_migration(self):
        """
        makemigrations properly constructs an empty migration.
        """
        with self.temporary_migration_module() as migration_dir:
            call_command("makemigrations", "migrations", empty=True, verbosity=0)

            # Check for existing 0001_initial.py file in migration folder
            initial_file = os.path.join(migration_dir, "0001_initial.py")
            self.assertTrue(os.path.exists(initial_file))

            with open(initial_file, encoding="utf-8") as fp:
                content = fp.read()

                # Remove all whitespace to check for empty dependencies and
                # operations
                content = content.replace(" ", "")
                self.assertIn(
                    "dependencies=[]" if HAS_BLACK else "dependencies=[\n]", content
                )
                self.assertIn(
                    "operations=[]" if HAS_BLACK else "operations=[\n]", content
                )