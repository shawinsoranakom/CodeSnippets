def test_none_timeout(self):
        """A timeout of None means "cache forever"."""
        output = self.engine.render_to_string("first")
        self.assertEqual(output, "content")
        output = self.engine.render_to_string("second")
        self.assertEqual(output, "content")