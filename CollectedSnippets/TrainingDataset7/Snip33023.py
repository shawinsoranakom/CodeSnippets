def test_make_list01(self):
        output = self.engine.render_to_string("make_list01", {"a": mark_safe("&")})
        self.assertEqual(output, "['&']")