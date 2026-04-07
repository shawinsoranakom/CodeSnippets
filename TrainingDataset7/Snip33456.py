def test_builtins01(self):
        output = self.engine.render_to_string("builtins01")
        self.assertEqual(output, "True")