def test_content_access_unrendered(self):
        # unrendered response raises an exception when content is accessed
        response = self._response()
        self.assertFalse(response.is_rendered)
        with self.assertRaises(ContentNotRenderedError):
            response.content
        self.assertFalse(response.is_rendered)