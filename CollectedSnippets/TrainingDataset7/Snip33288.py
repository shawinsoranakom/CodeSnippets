def test_i18n21(self):
        output = self.engine.render_to_string("i18n21", {"andrew": mark_safe("a & b")})
        self.assertEqual(output, "a & b")