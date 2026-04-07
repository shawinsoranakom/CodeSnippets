def test_i18n18(self):
        output = self.engine.render_to_string("i18n18", {"anton": "α & β"})
        self.assertEqual(output, "α &amp; β")