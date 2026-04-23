def test_nested_glob_recursive(self, mocked_modules, notify_mock):
        inner_py_file = self.ensure_file(self.tempdir / "dir" / "file.py")
        self.reloader.watch_dir(self.tempdir, "**/*.py")
        self.reloader.watch_dir(inner_py_file.parent, "**/*.py")
        with self.tick_twice():
            self.increment_mtime(inner_py_file)
        self.assertEqual(notify_mock.call_count, 1)
        self.assertCountEqual(notify_mock.call_args[0], [inner_py_file])