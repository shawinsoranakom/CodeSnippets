def test_urlize03(self):
        output = self.engine.render_to_string("urlize03", {"a": mark_safe("a &amp; b")})
        self.assertEqual(output, "a &amp; b")