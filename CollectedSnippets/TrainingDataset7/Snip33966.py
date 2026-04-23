def test_simpletag_renamed02(self):
        output = self.engine.render_to_string("simpletag-renamed02")
        self.assertEqual(output, "5")