def test_chaining13(self):
        output = self.engine.render_to_string("chaining13", {"a": "a < b"})
        self.assertEqual(output, "a &lt; b")