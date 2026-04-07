def test_cycle27(self):
        output = self.engine.render_to_string("cycle27", {"a": "<", "b": ">"})
        self.assertEqual(output, "<>")