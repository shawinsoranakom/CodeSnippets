def test_builtins02(self):
        output = self.engine.render_to_string("builtins02")
        self.assertEqual(output, "False")