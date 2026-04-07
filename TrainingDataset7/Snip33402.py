def test_autoescape_stringiterations01(self):
        """
        Iterating over strings outputs safe characters.
        """
        output = self.engine.render_to_string(
            "autoescape-stringiterations01", {"var": "K&R"}
        )
        self.assertEqual(output, "K,&amp;,R,")