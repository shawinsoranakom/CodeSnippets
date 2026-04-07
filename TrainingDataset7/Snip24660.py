def test_unit_conversions(self):
        "Testing default units during maths"
        d1 = D(m=100)
        d2 = D(km=1)

        d3 = d1 + d2
        self.assertEqual(d3._default_unit, "m")
        d4 = d2 + d1
        self.assertEqual(d4._default_unit, "km")
        d5 = d1 * 2
        self.assertEqual(d5._default_unit, "m")
        d6 = d1 / 2
        self.assertEqual(d6._default_unit, "m")