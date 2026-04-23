def test_legacyi18n17(self):
        output = self.engine.render_to_string("legacyi18n17", {"anton": "α & β"})
        self.assertEqual(output, "α &amp; β")