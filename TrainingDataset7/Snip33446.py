def test_ignores_strings_that_look_like_format_interpolation(self):
        output = self.engine.render_to_string("tpl-str")
        self.assertEqual(output, "%s")
        output = self.engine.render_to_string("tpl-percent")
        self.assertEqual(output, "%%")
        output = self.engine.render_to_string("tpl-weird-percent")
        self.assertEqual(output, "% %s")