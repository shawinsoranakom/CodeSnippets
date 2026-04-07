def test_basic_syntax36(self):
        output = self.engine.render_to_string("basic-syntax36", {"1": "abc"})
        self.assertEqual(output, "1.2")