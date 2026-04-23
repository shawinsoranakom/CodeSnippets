def test_chaining06(self):
        output = self.engine.render_to_string("chaining06", {"a": "a < b"})
        self.assertEqual(output, "A &lt; b")