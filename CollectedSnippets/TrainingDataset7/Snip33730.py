def test_if_tag_not18(self):
        output = self.engine.render_to_string(
            "if-tag-not18", {"foo": True, "bar": False}
        )
        self.assertEqual(output, "yes")