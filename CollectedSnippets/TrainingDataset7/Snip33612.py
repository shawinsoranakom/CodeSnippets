def test_firstof01(self):
        output = self.engine.render_to_string("firstof01", {"a": 0, "c": 0, "b": 0})
        self.assertEqual(output, "")