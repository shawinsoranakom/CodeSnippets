def test_linearref(self):
        "Testing linear referencing"

        ls = fromstr("LINESTRING(0 0, 0 10, 10 10, 10 0)")
        mls = fromstr("MULTILINESTRING((0 0, 0 10), (10 0, 10 10))")

        self.assertEqual(ls.project(Point(0, 20)), 10.0)
        self.assertEqual(ls.project(Point(7, 6)), 24)
        self.assertEqual(ls.project_normalized(Point(0, 20)), 1.0 / 3)

        self.assertEqual(ls.interpolate(10), Point(0, 10))
        self.assertEqual(ls.interpolate(24), Point(10, 6))
        self.assertEqual(ls.interpolate_normalized(1.0 / 3), Point(0, 10))

        self.assertEqual(mls.project(Point(0, 20)), 10)
        self.assertEqual(mls.project(Point(7, 6)), 16)

        self.assertEqual(mls.interpolate(9), Point(0, 9))
        self.assertEqual(mls.interpolate(17), Point(10, 7))