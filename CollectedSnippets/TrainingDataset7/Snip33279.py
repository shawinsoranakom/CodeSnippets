def test_legacyi18n04(self):
        """simple translation of a variable and filter"""
        output = self.engine.render_to_string("legacyi18n04", {"anton": "Å"})
        self.assertEqual(output, "å")