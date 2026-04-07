def test_if_tag03(self):
        output = self.engine.render_to_string("if-tag03")
        self.assertEqual(output, "no")