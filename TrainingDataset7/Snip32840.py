def test_chaining07(self):
        output = self.engine.render_to_string("chaining07", {"a": "a < b"})
        self.assertEqual(output, "a &amp;lt b")