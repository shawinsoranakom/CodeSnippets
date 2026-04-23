def test_firstof04(self):
        output = self.engine.render_to_string("firstof04", {"a": 0, "c": 3, "b": 0})
        self.assertEqual(output, "3")