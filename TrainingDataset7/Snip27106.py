def test_makemigration_merge_dry_run(self):
        """
        makemigrations respects --dry-run option when fixing migration
        conflicts (#24427).
        """
        out = io.StringIO()
        with self.temporary_migration_module(
            module="migrations.test_migrations_conflict"
        ) as migration_dir:
            call_command(
                "makemigrations",
                "migrations",
                name="merge",
                dry_run=True,
                merge=True,
                interactive=False,
                stdout=out,
            )
            merge_file = os.path.join(migration_dir, "0003_merge.py")
            self.assertFalse(os.path.exists(merge_file))
        output = out.getvalue()
        self.assertIn("Merging migrations", output)
        self.assertIn("Branch 0002_second", output)
        self.assertIn("Branch 0002_conflicting_second", output)
        self.assertNotIn("Created new merge migration", output)