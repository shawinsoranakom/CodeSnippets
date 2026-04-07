def test_makemigrations_merge_no_conflict(self):
        """
        makemigrations exits if in merge mode with no conflicts.
        """
        out = io.StringIO()
        with self.temporary_migration_module(module="migrations.test_migrations"):
            call_command("makemigrations", merge=True, stdout=out)
        self.assertIn("No conflicts detected to merge.", out.getvalue())