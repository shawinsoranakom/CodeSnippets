def test_access(self):
        "Testing access in different units"
        d = D(m=100)
        self.assertEqual(d.km, 0.1)
        self.assertAlmostEqual(d.ft, 328.084, 3)