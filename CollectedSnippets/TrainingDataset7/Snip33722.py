def test_if_tag_not10(self):
        output = self.engine.render_to_string(
            "if-tag-not10", {"foo": False, "bar": False}
        )
        self.assertEqual(output, "no")