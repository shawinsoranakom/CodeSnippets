def test_length07(self):
        output = self.engine.render_to_string("length07", {"None": None})
        self.assertEqual(output, "0")