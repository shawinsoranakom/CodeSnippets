def test_legacyi18n07(self):
        """translation of singular form"""
        output = self.engine.render_to_string("legacyi18n07", {"number": 1})
        self.assertEqual(output, "singular")