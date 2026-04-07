def test_translate(self):
        xfac, yfac = 5, -23
        qs = Country.objects.annotate(
            translated=functions.Translate("mpoly", xfac, yfac)
        )
        for c in qs:
            for p1, p2 in zip(c.mpoly, c.translated):
                for r1, r2 in zip(p1, p2):
                    for c1, c2 in zip(r1.coords, r2.coords):
                        # The low precision is for SpatiaLite
                        self.assertAlmostEqual(c1[0] + xfac, c2[0], 5)
                        self.assertAlmostEqual(c1[1] + yfac, c2[1], 5)