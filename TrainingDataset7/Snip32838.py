def test_chaining05(self):
        output = self.engine.render_to_string("chaining05", {"a": "a < b"})
        self.assertEqual(output, "A &lt; b")