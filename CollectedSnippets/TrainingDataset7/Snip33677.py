def test_if_tag_eq01(self):
        output = self.engine.render_to_string("if-tag-eq01")
        self.assertEqual(output, "yes")