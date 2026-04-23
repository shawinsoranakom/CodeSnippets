def test_builtins03(self):
        output = self.engine.render_to_string("builtins03")
        self.assertEqual(output, "None")