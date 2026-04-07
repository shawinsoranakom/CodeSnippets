def test_hash(self):
        a1 = A(sq_m=100)
        a2 = A(sq_m=1000000)
        a3 = A(sq_km=1)
        self.assertEqual(hash(a2), hash(a3))
        self.assertNotEqual(hash(a1), hash(a2))
        self.assertNotEqual(hash(a1), hash(a3))