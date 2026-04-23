def test_make_list02(self):
        output = self.engine.render_to_string("make_list02", {"a": mark_safe("&")})
        self.assertEqual(output, "[&#x27;&amp;&#x27;]")