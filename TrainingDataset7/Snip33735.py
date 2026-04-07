def test_if_tag_not23(self):
        output = self.engine.render_to_string(
            "if-tag-not23", {"foo": True, "bar": False}
        )
        self.assertEqual(output, "no")