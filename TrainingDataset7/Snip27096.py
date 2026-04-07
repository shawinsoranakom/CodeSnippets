def test_makemigrations_auto_merge_name(self, mock_datetime):
        mock_datetime.datetime.now.return_value = datetime.datetime(2016, 1, 2, 3, 4)
        with mock.patch("builtins.input", mock.Mock(return_value="y")):
            out = io.StringIO()
            with self.temporary_migration_module(
                module="migrations.test_migrations_conflict_long_name"
            ) as migration_dir:
                call_command(
                    "makemigrations",
                    "migrations",
                    merge=True,
                    interactive=True,
                    stdout=out,
                )
                merge_file = os.path.join(migration_dir, "0003_merge_20160102_0304.py")
                self.assertTrue(os.path.exists(merge_file))
            self.assertIn("Created new merge migration", out.getvalue())