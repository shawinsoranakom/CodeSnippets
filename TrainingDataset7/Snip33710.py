def test_if_tag_or04(self):
        output = self.engine.render_to_string(
            "if-tag-or04", {"foo": False, "bar": False}
        )
        self.assertEqual(output, "no")