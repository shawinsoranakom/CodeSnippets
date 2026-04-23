def test_setdefault(self):
        c = Context()

        x = c.setdefault("x", 42)
        self.assertEqual(x, 42)
        self.assertEqual(c["x"], 42)

        x = c.setdefault("x", 100)
        self.assertEqual(x, 42)
        self.assertEqual(c["x"], 42)