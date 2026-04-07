def test_if_tag_and07(self):
        output = self.engine.render_to_string("if-tag-and07", {"foo": True})
        self.assertEqual(output, "no")