def test_special_prefix(self):
        """No URLs are served if prefix contains a netloc part."""
        self.assertEqual(static("http://example.org"), [])
        self.assertEqual(static("//example.org"), [])