def test_content_access_rendered(self):
        # rendered response content can be accessed
        response = self._response().render()
        self.assertEqual(response.content, b"foo")