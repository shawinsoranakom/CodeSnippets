def test_if_tag_not02(self):
        output = self.engine.render_to_string("if-tag-not02", {"foo": True})
        self.assertEqual(output, "no")