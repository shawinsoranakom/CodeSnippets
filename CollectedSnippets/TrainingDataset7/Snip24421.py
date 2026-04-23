def test01_PointMutations(self):
        "Testing Point mutations"
        for p in (Point(1, 2, 3), fromstr("POINT (1 2 3)")):
            with self.subTest(p=p):
                self.assertEqual(
                    p._get_single_external(1), 2.0, "Point _get_single_external"
                )

                # _set_single
                p._set_single(0, 100)
                self.assertEqual(p.coords, (100.0, 2.0, 3.0), "Point _set_single")

                # _set_list
                p._set_list(2, (50, 3141))
                self.assertEqual(p.coords, (50.0, 3141.0), "Point _set_list")