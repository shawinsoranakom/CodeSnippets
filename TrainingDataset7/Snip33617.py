def test_firstof06(self):
        output = self.engine.render_to_string("firstof06", {"c": 3, "b": 0})
        self.assertEqual(output, "3")