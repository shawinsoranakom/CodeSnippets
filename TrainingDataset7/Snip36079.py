def test_snapshot_files_ignores_missing_files(self):
        with mock.patch.object(
            self.reloader, "watched_files", return_value=[self.nonexistent_file]
        ):
            self.assertEqual(dict(self.reloader.snapshot_files()), {})