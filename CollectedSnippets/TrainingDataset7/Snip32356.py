def assertFileContains(self, filepath, text):
        self.assertIn(
            text,
            self._get_file(filepath),
            "'%s' not in '%s'" % (text, filepath),
        )