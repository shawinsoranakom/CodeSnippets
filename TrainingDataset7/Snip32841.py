def test_chaining08(self):
        output = self.engine.render_to_string("chaining08", {"a": "a < b"})
        self.assertEqual(output, "a &lt b")