def test_add06(self):
        output = self.engine.render_to_string("add06", {"t1": (3, 4), "t2": (1, 2)})
        self.assertEqual(output, "(3, 4, 1, 2)")