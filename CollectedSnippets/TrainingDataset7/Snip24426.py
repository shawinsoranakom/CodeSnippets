def test06_Collection(self):
        "Testing Collection mutations"
        points = (
            MultiPoint(*map(Point, ((3, 4), (-1, 2), (5, -4), (2, 8)))),
            fromstr("MULTIPOINT (3 4,-1 2,5 -4,2 8)"),
        )
        for mp in points:
            with self.subTest(mp=mp):
                self.assertEqual(
                    mp._get_single_external(2),
                    Point(5, -4),
                    "Collection _get_single_external",
                )

                mp._set_list(3, map(Point, ((5, 5), (3, -2), (8, 1))))
                self.assertEqual(
                    mp.coords,
                    ((5.0, 5.0), (3.0, -2.0), (8.0, 1.0)),
                    "Collection _set_list",
                )

                lsa = MultiPoint(*map(Point, ((5, 5), (3, -2), (8, 1))))
                for f in geos_function_tests:
                    with self.subTest(f=f):
                        self.assertEqual(f(lsa), f(mp), "MultiPoint " + f.__name__)