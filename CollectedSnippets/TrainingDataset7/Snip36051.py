def test_overlapping_globs(self, mocked_modules, notify_mock):
        self.reloader.watch_dir(self.tempdir, "*.py")
        self.reloader.watch_dir(self.tempdir, "*.p*")
        with self.tick_twice():
            self.increment_mtime(self.existing_file)
        self.assertEqual(notify_mock.call_count, 1)
        self.assertCountEqual(notify_mock.call_args[0], [self.existing_file])