def test_if_tag_not08(self):
        output = self.engine.render_to_string(
            "if-tag-not08", {"foo": True, "bar": False}
        )
        self.assertEqual(output, "yes")