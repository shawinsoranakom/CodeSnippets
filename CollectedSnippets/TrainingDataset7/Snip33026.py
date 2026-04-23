def test_make_list04(self):
        output = self.engine.render_to_string("make_list04", {"a": mark_safe("&")})
        self.assertEqual(output, "['&']")