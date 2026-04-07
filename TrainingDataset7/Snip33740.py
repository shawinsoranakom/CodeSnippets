def test_if_tag_not28(self):
        output = self.engine.render_to_string(
            "if-tag-not28", {"foo": True, "bar": False}
        )
        self.assertEqual(output, "no")