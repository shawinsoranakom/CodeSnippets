def test04_LineStringMutations(self):
        "Testing LineString mutations"
        for ls in (
            LineString((1, 0), (4, 1), (6, -1)),
            fromstr("LINESTRING (1 0,4 1,6 -1)"),
        ):
            with self.subTest(ls=ls):
                self.assertEqual(
                    ls._get_single_external(1),
                    (4.0, 1.0),
                    "LineString _get_single_external",
                )

                # _set_single
                ls._set_single(0, (-50, 25))
                self.assertEqual(
                    ls.coords,
                    ((-50.0, 25.0), (4.0, 1.0), (6.0, -1.0)),
                    "LineString _set_single",
                )

                # _set_list
                ls._set_list(2, ((-50.0, 25.0), (6.0, -1.0)))
                self.assertEqual(
                    ls.coords, ((-50.0, 25.0), (6.0, -1.0)), "LineString _set_list"
                )

                lsa = LineString(ls.coords)
                for f in geos_function_tests:
                    with self.subTest(f=f):
                        self.assertEqual(f(lsa), f(ls), "LineString " + f.__name__)