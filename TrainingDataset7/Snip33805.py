def test_include06(self):
        output = self.engine.render_to_string("include06")
        self.assertEqual(output, "template with a space")