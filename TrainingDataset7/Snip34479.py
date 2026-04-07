def test_set_content(self):
        # content can be overridden
        response = self._response()
        self.assertFalse(response.is_rendered)
        response.content = "spam"
        self.assertTrue(response.is_rendered)
        self.assertEqual(response.content, b"spam")
        response.content = "baz"
        self.assertEqual(response.content, b"baz")