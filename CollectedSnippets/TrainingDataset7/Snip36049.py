def test_glob(self, mocked_modules, notify_mock):
        non_py_file = self.ensure_file(self.tempdir / "non_py_file")
        self.reloader.watch_dir(self.tempdir, "*.py")
        with self.tick_twice():
            self.increment_mtime(non_py_file)
            self.increment_mtime(self.existing_file)
        self.assertEqual(notify_mock.call_count, 1)
        self.assertCountEqual(notify_mock.call_args[0], [self.existing_file])