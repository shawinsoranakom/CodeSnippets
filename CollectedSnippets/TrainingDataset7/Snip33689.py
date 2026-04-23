def test_if_tag_gte_01(self):
        output = self.engine.render_to_string("if-tag-gte-01")
        self.assertEqual(output, "yes")