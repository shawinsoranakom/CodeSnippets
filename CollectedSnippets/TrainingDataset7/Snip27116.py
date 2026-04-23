def test_makemigrations_interactive_by_default(self):
        """
        The user is prompted to merge by default if there are conflicts and
        merge is True. Answer negative to differentiate it from behavior when
        --noinput is specified.
        """
        # Monkeypatch interactive questioner to auto reject
        out = io.StringIO()
        with mock.patch("builtins.input", mock.Mock(return_value="N")):
            with self.temporary_migration_module(
                module="migrations.test_migrations_conflict"
            ) as migration_dir:
                call_command(
                    "makemigrations", "migrations", name="merge", merge=True, stdout=out
                )
                merge_file = os.path.join(migration_dir, "0003_merge.py")
                # This will fail if interactive is False by default
                self.assertFalse(os.path.exists(merge_file))
            self.assertNotIn("Created new merge migration", out.getvalue())