def test_if_tag_not24(self):
        output = self.engine.render_to_string(
            "if-tag-not24", {"foo": False, "bar": True}
        )
        self.assertEqual(output, "yes")