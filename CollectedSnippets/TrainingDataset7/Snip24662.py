def test_units_str(self):
        "Testing conversion to strings"
        d1 = D(m=100)
        d2 = D(km=3.5)

        self.assertEqual(str(d1), "100.0 m")
        self.assertEqual(str(d2), "3.5 km")
        self.assertEqual(repr(d1), "Distance(m=100.0)")
        self.assertEqual(repr(d2), "Distance(km=3.5)")