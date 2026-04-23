def test_if_tag_and04(self):
        output = self.engine.render_to_string(
            "if-tag-and04", {"foo": False, "bar": False}
        )
        self.assertEqual(output, "no")