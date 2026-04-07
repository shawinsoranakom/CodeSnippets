def test_if_tag_and03(self):
        output = self.engine.render_to_string(
            "if-tag-and03", {"foo": False, "bar": True}
        )
        self.assertEqual(output, "no")