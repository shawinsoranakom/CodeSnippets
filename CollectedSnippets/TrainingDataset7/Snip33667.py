def test_if_tag06(self):
        output = self.engine.render_to_string("if-tag06")
        self.assertEqual(output, "")