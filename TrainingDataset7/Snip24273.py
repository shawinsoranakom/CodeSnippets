def test_left_right_lookups(self):
        "Testing the 'left' and 'right' lookup types."
        # Left: A << B => true if xmax(A) < xmin(B)
        # Right: A >> B => true if xmin(A) > xmax(B)
        # See: BOX2D_left() and BOX2D_right() in lwgeom_box2dfloat4.c in
        # PostGIS source.

        # Getting the borders for Colorado & Kansas
        co_border = State.objects.get(name="Colorado").poly
        ks_border = State.objects.get(name="Kansas").poly

        # Note: Wellington has an 'X' value of 174, so it will not be
        # considered to the left of CO.

        # These cities should be strictly to the right of the CO border.
        cities = [
            "Houston",
            "Dallas",
            "Oklahoma City",
            "Lawrence",
            "Chicago",
            "Wellington",
        ]
        qs = City.objects.filter(point__right=co_border)
        self.assertEqual(6, len(qs))
        for c in qs:
            self.assertIn(c.name, cities)

        # These cities should be strictly to the right of the KS border.
        cities = ["Chicago", "Wellington"]
        qs = City.objects.filter(point__right=ks_border)
        self.assertEqual(2, len(qs))
        for c in qs:
            self.assertIn(c.name, cities)

        # Note: Wellington has an 'X' value of 174, so it will not be
        # considered
        #  to the left of CO.
        vic = City.objects.get(point__left=co_border)
        self.assertEqual("Victoria", vic.name)

        cities = ["Pueblo", "Victoria"]
        qs = City.objects.filter(point__left=ks_border)
        self.assertEqual(2, len(qs))
        for c in qs:
            self.assertIn(c.name, cities)