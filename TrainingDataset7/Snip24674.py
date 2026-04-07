def test_comparisons(self):
        "Testing comparisons"
        a1 = A(sq_m=100)
        a2 = A(sq_km=1)
        a3 = A(sq_km=0)

        self.assertGreater(a2, a1)
        self.assertEqual(a1, a1)
        self.assertLess(a1, a2)
        self.assertFalse(a3)