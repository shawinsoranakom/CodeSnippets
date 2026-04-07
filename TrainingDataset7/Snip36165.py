def test_contains(self):
        s = OrderedSet()
        self.assertEqual(len(s), 0)
        s.add(1)
        self.assertIn(1, s)