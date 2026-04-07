def test_if_tag_not20(self):
        output = self.engine.render_to_string(
            "if-tag-not20", {"foo": False, "bar": False}
        )
        self.assertEqual(output, "yes")