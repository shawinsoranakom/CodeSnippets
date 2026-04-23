def test_makemigrations_interactive_reject(self):
        """
        makemigrations enters and exits interactive mode properly.
        """
        # Monkeypatch interactive questioner to auto reject
        with mock.patch("builtins.input", mock.Mock(return_value="N")):
            with self.temporary_migration_module(
                module="migrations.test_migrations_conflict"
            ) as migration_dir:
                with captured_stdout():
                    call_command(
                        "makemigrations",
                        "migrations",
                        name="merge",
                        merge=True,
                        interactive=True,
                        verbosity=0,
                    )
                merge_file = os.path.join(migration_dir, "0003_merge.py")
                self.assertFalse(os.path.exists(merge_file))