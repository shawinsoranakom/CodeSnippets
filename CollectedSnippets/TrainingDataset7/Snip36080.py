def test_snapshot_files_updates(self):
        with mock.patch.object(
            self.reloader, "watched_files", return_value=[self.existing_file]
        ):
            snapshot1 = dict(self.reloader.snapshot_files())
            self.assertIn(self.existing_file, snapshot1)
            self.increment_mtime(self.existing_file)
            snapshot2 = dict(self.reloader.snapshot_files())
            self.assertNotEqual(
                snapshot1[self.existing_file], snapshot2[self.existing_file]
            )