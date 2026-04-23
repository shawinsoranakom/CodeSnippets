def test_if_tag_or05(self):
        output = self.engine.render_to_string("if-tag-or05", {"foo": False})
        self.assertEqual(output, "no")