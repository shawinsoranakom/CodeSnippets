def test_overlapping_glob_recursive(self, mocked_modules, notify_mock):
        py_file = self.ensure_file(self.tempdir / "dir" / "file.py")
        self.reloader.watch_dir(self.tempdir, "**/*.p*")
        self.reloader.watch_dir(self.tempdir, "**/*.py*")
        with self.tick_twice():
            self.increment_mtime(py_file)
        self.assertEqual(notify_mock.call_count, 1)
        self.assertCountEqual(notify_mock.call_args[0], [py_file])