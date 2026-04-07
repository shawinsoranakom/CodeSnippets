def test_hash(self):
        d1 = D(m=99)
        d2 = D(m=100)
        d3 = D(km=0.1)
        self.assertEqual(hash(d2), hash(d3))
        self.assertNotEqual(hash(d1), hash(d2))
        self.assertNotEqual(hash(d1), hash(d3))