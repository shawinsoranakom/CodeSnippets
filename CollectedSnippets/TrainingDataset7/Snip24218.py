def test_rotate(self):
        angle = math.pi
        tests = [
            {"angle": angle},
            {"angle": angle, "origin": Point(0, 0)},
            {"angle": angle, "origin": Point(1, 1)},
        ]
        for params in tests:
            with self.subTest(params=params):
                qs = Country.objects.annotate(
                    rotated=functions.Rotate("mpoly", **params)
                )
                for country in qs:
                    for p1, p2 in zip(country.mpoly, country.rotated):
                        for r1, r2 in zip(p1, p2):
                            for c1, c2 in zip(r1.coords, r2.coords):
                                origin = params.get("origin")
                                if origin is None:
                                    origin = Point(0, 0)
                                self.assertAlmostEqual(-c1[0] + 2 * origin.x, c2[0], 5)
                                self.assertAlmostEqual(-c1[1] + 2 * origin.y, c2[1], 5)