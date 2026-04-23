def test_if_tag_or03(self):
        output = self.engine.render_to_string(
            "if-tag-or03", {"foo": False, "bar": True}
        )
        self.assertEqual(output, "yes")