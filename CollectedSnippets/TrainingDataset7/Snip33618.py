def test_firstof07(self):
        output = self.engine.render_to_string("firstof07", {"a": 0})
        self.assertEqual(output, "c")