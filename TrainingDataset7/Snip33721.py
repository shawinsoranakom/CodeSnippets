def test_if_tag_not09(self):
        output = self.engine.render_to_string(
            "if-tag-not09", {"foo": False, "bar": True}
        )
        self.assertEqual(output, "no")