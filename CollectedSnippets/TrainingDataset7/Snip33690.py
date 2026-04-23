def test_if_tag_gte_02(self):
        output = self.engine.render_to_string("if-tag-gte-02")
        self.assertEqual(output, "no")