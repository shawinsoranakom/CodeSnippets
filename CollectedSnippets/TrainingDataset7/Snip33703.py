def test_if_tag_and05(self):
        output = self.engine.render_to_string("if-tag-and05", {"foo": False})
        self.assertEqual(output, "no")