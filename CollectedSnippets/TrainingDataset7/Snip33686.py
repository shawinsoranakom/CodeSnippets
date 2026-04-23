def test_if_tag_noteq05(self):
        output = self.engine.render_to_string("if-tag-noteq05")
        self.assertEqual(output, "yes")