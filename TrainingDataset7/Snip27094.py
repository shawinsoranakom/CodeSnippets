def test_makemigrations_interactive_accept(self):
        """
        makemigrations enters interactive mode and merges properly.
        """
        # Monkeypatch interactive questioner to auto accept
        with mock.patch("builtins.input", mock.Mock(return_value="y")):
            out = io.StringIO()
            with self.temporary_migration_module(
                module="migrations.test_migrations_conflict"
            ) as migration_dir:
                call_command(
                    "makemigrations",
                    "migrations",
                    name="merge",
                    merge=True,
                    interactive=True,
                    stdout=out,
                )
                merge_file = os.path.join(migration_dir, "0003_merge.py")
                self.assertTrue(os.path.exists(merge_file))
            self.assertIn("Created new merge migration", out.getvalue())