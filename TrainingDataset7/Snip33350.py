def test_i18n20(self):
        output = self.engine.render_to_string("i18n20", {"andrew": "a & b"})
        self.assertEqual(output, "a &amp; b")