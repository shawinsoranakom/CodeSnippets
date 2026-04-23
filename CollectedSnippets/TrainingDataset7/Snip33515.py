def test_cycle26(self):
        output = self.engine.render_to_string("cycle26", {"a": "<", "b": ">"})
        self.assertEqual(output, "&lt;&gt;")