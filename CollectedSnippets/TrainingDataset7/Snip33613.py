def test_firstof02(self):
        output = self.engine.render_to_string("firstof02", {"a": 1, "c": 0, "b": 0})
        self.assertEqual(output, "1")