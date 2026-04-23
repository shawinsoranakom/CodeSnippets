def test_firstof11(self):
        output = self.engine.render_to_string("firstof11", {"a": "<", "b": ">"})
        self.assertEqual(output, "&lt;")