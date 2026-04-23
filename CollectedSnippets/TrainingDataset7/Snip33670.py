def test_if_tag09(self):
        output = self.engine.render_to_string("if-tag09")
        self.assertEqual(output, "nothing")