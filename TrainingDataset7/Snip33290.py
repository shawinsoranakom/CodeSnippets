def test_legacyi18n18(self):
        output = self.engine.render_to_string("legacyi18n18", {"anton": "α & β"})
        self.assertEqual(output, "α &amp; β")