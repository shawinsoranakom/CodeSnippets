def test_if_tag_lt_01(self):
        output = self.engine.render_to_string("if-tag-lt-01")
        self.assertEqual(output, "yes")