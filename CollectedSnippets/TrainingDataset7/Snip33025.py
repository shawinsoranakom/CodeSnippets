def test_make_list03(self):
        output = self.engine.render_to_string("make_list03", {"a": mark_safe("&")})
        self.assertEqual(output, "['&']")