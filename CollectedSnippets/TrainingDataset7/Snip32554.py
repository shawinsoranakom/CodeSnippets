def assertFileContains(self, filepath, text):
        self.assertContains(self._response(filepath), text)