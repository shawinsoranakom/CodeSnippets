def test_if_tag_or06(self):
        output = self.engine.render_to_string("if-tag-or06", {"bar": False})
        self.assertEqual(output, "no")