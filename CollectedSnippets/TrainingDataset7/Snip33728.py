def test_if_tag_not16(self):
        output = self.engine.render_to_string("if-tag-not16")
        self.assertEqual(output, "yes")