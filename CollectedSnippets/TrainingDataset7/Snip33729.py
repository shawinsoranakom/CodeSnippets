def test_if_tag_not17(self):
        output = self.engine.render_to_string(
            "if-tag-not17", {"foo": True, "bar": True}
        )
        self.assertEqual(output, "yes")