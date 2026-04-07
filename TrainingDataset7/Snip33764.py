def test_if_tag_badarg02(self):
        output = self.engine.render_to_string("if-tag-badarg02", {"y": 0})
        self.assertEqual(output, "")