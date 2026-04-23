def test_upload_multiple_files_error(self):
        """Uploading multiple files will error"""
        file_1 = MockFile("file1", b"123")
        file_2 = MockFile("file2", b"456")

        params = {
            file_1.name: file_1.data,
            file_2.name: file_2.data,
            "sessionId": (None, "mockSessionId"),
            "widgetId": (None, "mockWidgetId"),
        }
        response = self._upload_files(params)
        self.assertEqual(400, response.code)
        self.assertIn("Expected 1 file, but got 2", response.reason)