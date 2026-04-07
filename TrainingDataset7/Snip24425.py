def test05_Polygon(self):
        "Testing Polygon mutations"
        for pg in (
            Polygon(
                ((1, 0), (4, 1), (6, -1), (8, 10), (1, 0)),
                ((5, 4), (6, 4), (6, 3), (5, 4)),
            ),
            fromstr("POLYGON ((1 0,4 1,6 -1,8 10,1 0),(5 4,6 4,6 3,5 4))"),
        ):
            with self.subTest(pg=pg):
                self.assertEqual(
                    pg._get_single_external(0),
                    LinearRing((1, 0), (4, 1), (6, -1), (8, 10), (1, 0)),
                    "Polygon _get_single_external(0)",
                )
                self.assertEqual(
                    pg._get_single_external(1),
                    LinearRing((5, 4), (6, 4), (6, 3), (5, 4)),
                    "Polygon _get_single_external(1)",
                )

                # _set_list
                pg._set_list(
                    2,
                    (
                        ((1, 2), (10, 0), (12, 9), (-1, 15), (1, 2)),
                        ((4, 2), (5, 2), (5, 3), (4, 2)),
                    ),
                )
                self.assertEqual(
                    pg.coords,
                    (
                        (
                            (1.0, 2.0),
                            (10.0, 0.0),
                            (12.0, 9.0),
                            (-1.0, 15.0),
                            (1.0, 2.0),
                        ),
                        ((4.0, 2.0), (5.0, 2.0), (5.0, 3.0), (4.0, 2.0)),
                    ),
                    "Polygon _set_list",
                )

                lsa = Polygon(*pg.coords)
                for f in geos_function_tests:
                    with self.subTest(f=f):
                        self.assertEqual(f(lsa), f(pg), "Polygon " + f.__name__)