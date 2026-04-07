def test_if_tag_not07(self):
        output = self.engine.render_to_string(
            "if-tag-not07", {"foo": True, "bar": True}
        )
        self.assertEqual(output, "no")