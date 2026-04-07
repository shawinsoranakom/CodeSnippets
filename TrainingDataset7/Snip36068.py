def test_watched_roots_contains_directory_globs(self):
        self.reloader.watch_dir(self.tempdir, "*.py")
        paths = self.reloader.watched_roots([])
        self.assertIn(self.tempdir, paths)