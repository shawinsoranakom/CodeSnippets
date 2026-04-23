def test_if_tag_not22(self):
        output = self.engine.render_to_string(
            "if-tag-not22", {"foo": True, "bar": True}
        )
        self.assertEqual(output, "yes")