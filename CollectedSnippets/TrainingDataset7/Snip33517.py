def test_cycle28(self):
        output = self.engine.render_to_string("cycle28", {"a": "<", "b": ">"})
        self.assertEqual(output, "<&gt;")