def test_if_tag_not32(self):
        output = self.engine.render_to_string(
            "if-tag-not32", {"foo": True, "bar": True}
        )
        self.assertEqual(output, "no")