def test_if_tag_not35(self):
        output = self.engine.render_to_string(
            "if-tag-not35", {"foo": False, "bar": False}
        )
        self.assertEqual(output, "yes")