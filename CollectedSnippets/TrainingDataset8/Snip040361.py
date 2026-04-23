def test_upload_missing_params_error(self):
        """Missing params in the body should fail with 400 status."""
        params = {
            "image.png": ("image.png", b"1234"),
            "fileId": (None, "123"),
            "sessionId": (None, "mockSessionId"),
            # "widgetId": (None, 'mockWidgetId'),
        }

        response = self._upload_files(params)
        self.assertEqual(400, response.code)
        self.assertIn("Missing 'widgetId'", response.reason)