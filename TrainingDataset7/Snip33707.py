def test_if_tag_or01(self):
        output = self.engine.render_to_string("if-tag-or01", {"foo": True, "bar": True})
        self.assertEqual(output, "yes")