def test_bool(self):
        # Refs #23664
        s = OrderedSet()
        self.assertFalse(s)
        s.add(1)
        self.assertTrue(s)