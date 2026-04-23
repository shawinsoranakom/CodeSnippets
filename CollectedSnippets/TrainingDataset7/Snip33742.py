def test_if_tag_not30(self):
        output = self.engine.render_to_string(
            "if-tag-not30", {"foo": False, "bar": False}
        )
        self.assertEqual(output, "yes")