def test_upload_one_file(self):
        """Uploading a file should populate our file_mgr."""
        file = MockFile("filename", b"123")
        params = {
            file.name: file.data,
            "sessionId": (None, "mockSessionId"),
            "widgetId": (None, "mockWidgetId"),
        }
        response = self._upload_files(params)
        self.assertEqual(200, response.code, response.reason)
        file_id = int(response.body)
        self.assertEqual(
            [(file_id, file.name, file.data)],
            [
                (rec.id, rec.name, rec.data)
                for rec in self.file_mgr.get_all_files("mockSessionId", "mockWidgetId")
            ],
        )