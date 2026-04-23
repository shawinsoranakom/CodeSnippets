def test_chaining10(self):
        output = self.engine.render_to_string("chaining10", {"a": "a < b"})
        self.assertEqual(output, "a &lt; b")