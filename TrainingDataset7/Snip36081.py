def test_snapshot_files_with_duplicates(self):
        with mock.patch.object(
            self.reloader,
            "watched_files",
            return_value=[self.existing_file, self.existing_file],
        ):
            snapshot = list(self.reloader.snapshot_files())
            self.assertEqual(len(snapshot), 1)
            self.assertEqual(snapshot[0][0], self.existing_file)