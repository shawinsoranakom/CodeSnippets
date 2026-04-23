def test_if_tag_and08(self):
        output = self.engine.render_to_string("if-tag-and08", {"bar": True})
        self.assertEqual(output, "no")