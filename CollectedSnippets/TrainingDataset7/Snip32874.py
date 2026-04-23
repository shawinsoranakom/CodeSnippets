def test_default03(self):
        output = self.engine.render_to_string("default03", {"a": mark_safe("x>")})
        self.assertEqual(output, "x>")