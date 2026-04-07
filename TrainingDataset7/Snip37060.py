def test_debug_off(self):
        """No URLs are served if DEBUG=False."""
        self.assertEqual(static("test"), [])