def test_default04(self):
        output = self.engine.render_to_string("default04", {"a": mark_safe("x>")})
        self.assertEqual(output, "x>")