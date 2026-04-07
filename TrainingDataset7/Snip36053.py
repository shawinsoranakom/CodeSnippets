def test_multiple_recursive_globs(self, mocked_modules, notify_mock):
        non_py_file = self.ensure_file(self.tempdir / "dir" / "test.txt")
        py_file = self.ensure_file(self.tempdir / "dir" / "file.py")
        self.reloader.watch_dir(self.tempdir, "**/*.txt")
        self.reloader.watch_dir(self.tempdir, "**/*.py")
        with self.tick_twice():
            self.increment_mtime(non_py_file)
            self.increment_mtime(py_file)
        self.assertEqual(notify_mock.call_count, 2)
        self.assertCountEqual(
            notify_mock.call_args_list, [mock.call(py_file), mock.call(non_py_file)]
        )