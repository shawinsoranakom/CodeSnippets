def test_if_tag_or07(self):
        output = self.engine.render_to_string("if-tag-or07", {"foo": True})
        self.assertEqual(output, "yes")