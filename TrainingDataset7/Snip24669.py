def test_access(self):
        "Testing access in different units"
        a = A(sq_m=100)
        self.assertEqual(a.sq_km, 0.0001)
        self.assertAlmostEqual(a.sq_ft, 1076.391, 3)