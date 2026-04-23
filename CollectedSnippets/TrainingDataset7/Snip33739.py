def test_if_tag_not27(self):
        output = self.engine.render_to_string(
            "if-tag-not27", {"foo": True, "bar": True}
        )
        self.assertEqual(output, "no")