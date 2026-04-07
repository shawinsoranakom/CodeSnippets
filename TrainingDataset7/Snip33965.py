def test_simpletag_renamed01(self):
        output = self.engine.render_to_string("simpletag-renamed01")
        self.assertEqual(output, "6")