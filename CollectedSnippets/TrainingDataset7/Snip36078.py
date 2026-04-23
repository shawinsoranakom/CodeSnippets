def test_tick_does_not_trigger_twice(self, mock_notify_file_changed):
        with mock.patch.object(
            self.reloader, "watched_files", return_value=[self.existing_file]
        ):
            ticker = self.reloader.tick()
            next(ticker)
            self.increment_mtime(self.existing_file)
            next(ticker)
            next(ticker)
            self.assertEqual(mock_notify_file_changed.call_count, 1)