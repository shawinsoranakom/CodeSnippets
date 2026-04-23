def test_multiple_globs(self, mocked_modules, notify_mock):
        self.ensure_file(self.tempdir / "x.test")
        self.reloader.watch_dir(self.tempdir, "*.py")
        self.reloader.watch_dir(self.tempdir, "*.test")
        with self.tick_twice():
            self.increment_mtime(self.existing_file)
        self.assertEqual(notify_mock.call_count, 1)
        self.assertCountEqual(notify_mock.call_args[0], [self.existing_file])