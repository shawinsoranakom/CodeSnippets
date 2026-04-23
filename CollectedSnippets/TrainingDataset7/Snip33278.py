def test_i18n04(self):
        """simple translation of a variable and filter"""
        output = self.engine.render_to_string("i18n04", {"anton": "Å"})
        self.assertEqual(output, "å")