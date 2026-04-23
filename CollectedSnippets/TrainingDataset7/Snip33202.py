def test_urlize04(self):
        output = self.engine.render_to_string("urlize04", {"a": mark_safe("a &amp; b")})
        self.assertEqual(output, "a &amp; b")