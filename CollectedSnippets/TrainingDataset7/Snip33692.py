def test_if_tag_lt_02(self):
        output = self.engine.render_to_string("if-tag-lt-02")
        self.assertEqual(output, "no")