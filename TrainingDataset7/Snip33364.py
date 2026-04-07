def test_trans_tag_using_a_string_that_looks_like_str_fmt(self):
        output = self.engine.render_to_string("template")
        self.assertEqual(output, "%s")