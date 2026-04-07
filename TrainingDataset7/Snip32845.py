def test_chaining12(self):
        output = self.engine.render_to_string("chaining12", {"a": "a < b"})
        self.assertEqual(output, "a < ")