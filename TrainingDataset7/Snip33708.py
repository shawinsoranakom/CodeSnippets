def test_if_tag_or02(self):
        output = self.engine.render_to_string(
            "if-tag-or02", {"foo": True, "bar": False}
        )
        self.assertEqual(output, "yes")