def test_if_tag_not01(self):
        output = self.engine.render_to_string("if-tag-not01", {"foo": True})
        self.assertEqual(output, "yes")