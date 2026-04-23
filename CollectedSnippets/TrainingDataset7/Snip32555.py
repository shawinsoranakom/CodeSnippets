def assertFileNotFound(self, filepath):
        self.assertEqual(self._response(filepath).status_code, 404)