def test_makemigrations_handle_merge(self):
        """
        makemigrations properly merges the conflicting migrations with
        --noinput.
        """
        out = io.StringIO()
        with self.temporary_migration_module(
            module="migrations.test_migrations_conflict"
        ) as migration_dir:
            call_command(
                "makemigrations",
                "migrations",
                name="merge",
                merge=True,
                interactive=False,
                stdout=out,
            )
            merge_file = os.path.join(migration_dir, "0003_merge.py")
            self.assertTrue(os.path.exists(merge_file))
        output = out.getvalue()
        self.assertIn("Merging migrations", output)
        self.assertIn("Branch 0002_second", output)
        self.assertIn("Branch 0002_conflicting_second", output)
        self.assertIn("Created new merge migration", output)