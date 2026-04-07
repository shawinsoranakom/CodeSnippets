def test_chaining11(self):
        output = self.engine.render_to_string("chaining11", {"a": "a < b"})
        self.assertEqual(output, "a < ")