def test_if_tag_and01(self):
        output = self.engine.render_to_string(
            "if-tag-and01", {"foo": True, "bar": True}
        )
        self.assertEqual(output, "yes")