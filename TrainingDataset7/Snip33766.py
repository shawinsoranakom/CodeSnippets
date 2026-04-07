def test_if_tag_badarg04(self):
        output = self.engine.render_to_string("if-tag-badarg04")
        self.assertEqual(output, "no")