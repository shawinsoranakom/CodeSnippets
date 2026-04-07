def test_if_tag_and02(self):
        output = self.engine.render_to_string(
            "if-tag-and02", {"foo": True, "bar": False}
        )
        self.assertEqual(output, "no")