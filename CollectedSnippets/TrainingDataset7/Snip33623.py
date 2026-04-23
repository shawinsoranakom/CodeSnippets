def test_firstof12(self):
        output = self.engine.render_to_string("firstof12", {"a": "", "b": ">"})
        self.assertEqual(output, "&gt;")