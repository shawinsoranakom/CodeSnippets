def test_watch_files_with_recursive_glob(self):
        inner_file = self.ensure_file(self.tempdir / "test" / "test.py")
        self.reloader.watch_dir(self.tempdir, "**/*.py")
        watched_files = list(self.reloader.watched_files())
        self.assertIn(self.existing_file, watched_files)
        self.assertIn(inner_file, watched_files)