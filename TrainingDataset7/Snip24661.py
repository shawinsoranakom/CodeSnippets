def test_comparisons(self):
        "Testing comparisons"
        d1 = D(m=100)
        d2 = D(km=1)
        d3 = D(km=0)

        self.assertGreater(d2, d1)
        self.assertEqual(d1, d1)
        self.assertLess(d1, d2)
        self.assertFalse(d3)