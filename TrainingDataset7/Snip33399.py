def test_autoescape_filters01(self):
        output = self.engine.render_to_string(
            "autoescape-filters01", {"var": "this & that"}
        )
        self.assertEqual(output, "this  that")