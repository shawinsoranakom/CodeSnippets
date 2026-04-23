def test_units_str(self):
        "Testing conversion to strings"
        a1 = A(sq_m=100)
        a2 = A(sq_km=3.5)

        self.assertEqual(str(a1), "100.0 sq_m")
        self.assertEqual(str(a2), "3.5 sq_km")
        self.assertEqual(repr(a1), "Area(sq_m=100.0)")
        self.assertEqual(repr(a2), "Area(sq_km=3.5)")