def test_watched_roots_contains_files(self):
        paths = self.reloader.watched_roots([self.existing_file])
        self.assertIn(self.existing_file.parent, paths)