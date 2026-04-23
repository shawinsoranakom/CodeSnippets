def test_i18n22(self):
        output = self.engine.render_to_string("i18n22", {"andrew": mark_safe("a & b")})
        self.assertEqual(output, "a & b")