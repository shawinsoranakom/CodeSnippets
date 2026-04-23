def test_chaining09(self):
        output = self.engine.render_to_string("chaining09", {"a": "a < b"})
        self.assertEqual(output, "a &lt; b")