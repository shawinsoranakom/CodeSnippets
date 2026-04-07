def test_len(self):
        s = OrderedSet()
        self.assertEqual(len(s), 0)
        s.add(1)
        s.add(2)
        s.add(2)
        self.assertEqual(len(s), 2)