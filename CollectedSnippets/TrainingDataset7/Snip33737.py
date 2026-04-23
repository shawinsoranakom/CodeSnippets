def test_if_tag_not25(self):
        output = self.engine.render_to_string(
            "if-tag-not25", {"foo": False, "bar": False}
        )
        self.assertEqual(output, "yes")