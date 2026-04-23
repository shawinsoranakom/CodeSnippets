def test_if_tag_eq05(self):
        output = self.engine.render_to_string("if-tag-eq05")
        self.assertEqual(output, "no")