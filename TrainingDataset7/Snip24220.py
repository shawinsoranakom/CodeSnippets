def test_scale(self):
        xfac, yfac = 2, 3
        tol = 5  # The low precision tolerance is for SpatiaLite
        qs = Country.objects.annotate(scaled=functions.Scale("mpoly", xfac, yfac))
        for country in qs:
            for p1, p2 in zip(country.mpoly, country.scaled):
                for r1, r2 in zip(p1, p2):
                    for c1, c2 in zip(r1.coords, r2.coords):
                        self.assertAlmostEqual(c1[0] * xfac, c2[0], tol)
                        self.assertAlmostEqual(c1[1] * yfac, c2[1], tol)
        # Test float/Decimal values
        qs = Country.objects.annotate(
            scaled=functions.Scale("mpoly", 1.5, Decimal("2.5"))
        )
        self.assertGreater(qs[0].scaled.area, qs[0].mpoly.area)