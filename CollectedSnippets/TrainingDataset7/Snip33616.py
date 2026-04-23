def test_firstof05(self):
        output = self.engine.render_to_string("firstof05", {"a": 1, "c": 3, "b": 2})
        self.assertEqual(output, "1")