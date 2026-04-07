def test_safe02(self):
        output = self.engine.render_to_string("safe02", {"a": "<b>hello</b>"})
        self.assertEqual(output, "<b>hello</b> -- <b>hello</b>")