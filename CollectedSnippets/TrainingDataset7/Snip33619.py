def test_firstof08(self):
        output = self.engine.render_to_string("firstof08", {"a": 0, "b": 0})
        self.assertEqual(output, "c and d")