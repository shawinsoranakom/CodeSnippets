def assertFileNotFound(self, filepath):
        with self.assertRaises(OSError):
            self._get_file(filepath)