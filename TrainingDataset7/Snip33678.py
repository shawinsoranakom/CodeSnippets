def test_if_tag_eq02(self):
        output = self.engine.render_to_string("if-tag-eq02", {"foo": 1})
        self.assertEqual(output, "no")