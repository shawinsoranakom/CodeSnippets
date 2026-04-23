def test_if_tag_and06(self):
        output = self.engine.render_to_string("if-tag-and06", {"bar": False})
        self.assertEqual(output, "no")