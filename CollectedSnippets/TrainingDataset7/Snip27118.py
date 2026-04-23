def test_makemigrations_unspecified_app_with_conflict_merge(self):
        """
        makemigrations does not create a merge for an unspecified app even if
        it has conflicting migrations.
        """
        # Monkeypatch interactive questioner to auto accept
        with mock.patch("builtins.input", mock.Mock(return_value="y")):
            out = io.StringIO()
            with self.temporary_migration_module(
                app_label="migrated_app"
            ) as migration_dir:
                call_command(
                    "makemigrations",
                    "migrated_app",
                    name="merge",
                    merge=True,
                    interactive=True,
                    stdout=out,
                )
                merge_file = os.path.join(migration_dir, "0003_merge.py")
                self.assertFalse(os.path.exists(merge_file))
            self.assertIn("No conflicts detected to merge.", out.getvalue())