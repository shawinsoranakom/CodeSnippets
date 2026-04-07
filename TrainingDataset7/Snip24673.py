def test_unit_conversions(self):
        "Testing default units during maths"
        a1 = A(sq_m=100)
        a2 = A(sq_km=1)

        a3 = a1 + a2
        self.assertEqual(a3._default_unit, "sq_m")
        a4 = a2 + a1
        self.assertEqual(a4._default_unit, "sq_km")
        a5 = a1 * 2
        self.assertEqual(a5._default_unit, "sq_m")
        a6 = a1 / 2
        self.assertEqual(a6._default_unit, "sq_m")