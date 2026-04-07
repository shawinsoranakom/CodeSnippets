def test_autoescape_lookup01(self):
        """
        Escape requirement survives lookup.
        """
        output = self.engine.render_to_string(
            "autoescape-lookup01", {"var": {"key": "this & that"}}
        )
        self.assertEqual(output, "this &amp; that")