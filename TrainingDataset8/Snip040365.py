def test_upload_one_file(self):
        """Upload should fail if the sessionId doesn't exist."""
        file = MockFile("filename", b"123")
        params = {
            file.name: file.data,
            "sessionId": (None, "mockSessionId"),
            "widgetId": (None, "mockWidgetId"),
        }
        response = self._upload_files(params)
        self.assertEqual(400, response.code)
        self.assertIn("Invalid session_id: 'mockSessionId'", response.reason)
        self.assertEqual(
            self.file_mgr.get_all_files("mockSessionId", "mockWidgetId"), []
        )