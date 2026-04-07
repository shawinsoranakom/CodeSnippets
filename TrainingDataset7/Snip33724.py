def test_if_tag_not12(self):
        output = self.engine.render_to_string(
            "if-tag-not12", {"foo": True, "bar": True}
        )
        self.assertEqual(output, "no")