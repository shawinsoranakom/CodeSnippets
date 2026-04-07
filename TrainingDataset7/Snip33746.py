def test_if_tag_not34(self):
        output = self.engine.render_to_string(
            "if-tag-not34", {"foo": False, "bar": True}
        )
        self.assertEqual(output, "yes")