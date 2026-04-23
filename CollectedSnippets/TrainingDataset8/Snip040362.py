def test_upload_missing_file_error(self):
        """Missing file should fail with 400 status."""
        params = {
            # "image.png": ("image.png", b"1234"),
            "fileId": (None, "123"),
            "sessionId": (None, "mockSessionId"),
            "widgetId": (None, "mockWidgetId"),
        }
        response = self._upload_files(params)
        self.assertEqual(400, response.code)
        self.assertIn("Expected 1 file, but got 0", response.reason)