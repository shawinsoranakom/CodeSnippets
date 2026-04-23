def test_legacyi18n26(self):
        output = self.engine.render_to_string(
            "legacyi18n26", {"myextra_field": "test", "number": 1}
        )
        self.assertEqual(output, "singular test")