def test_resetcycle07(self):
        output = self.engine.render_to_string("resetcycle07", {"test": list(range(5))})
        self.assertEqual(output, "aa-a+a-a+a-")