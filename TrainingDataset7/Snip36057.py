def test_watch_with_glob(self):
        self.reloader.watch_dir(self.tempdir, "*.py")
        watched_files = list(self.reloader.watched_files())
        self.assertIn(self.existing_file, watched_files)