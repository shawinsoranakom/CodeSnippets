def test_prepared(self):
        "Testing PreparedGeometry support."
        # Creating a simple multipolygon and getting a prepared version.
        mpoly = GEOSGeometry(
            "MULTIPOLYGON(((0 0,0 5,5 5,5 0,0 0)),((5 5,5 10,10 10,10 5,5 5)))"
        )
        prep = mpoly.prepared

        # A set of test points.
        pnts = [Point(5, 5), Point(7.5, 7.5), Point(2.5, 7.5)]
        for pnt in pnts:
            # Results should be the same (but faster)
            with self.subTest(pnt=pnt):
                self.assertEqual(mpoly.contains(pnt), prep.contains(pnt))
                self.assertEqual(mpoly.intersects(pnt), prep.intersects(pnt))
                self.assertEqual(mpoly.covers(pnt), prep.covers(pnt))

        self.assertTrue(prep.crosses(fromstr("LINESTRING(1 1, 15 15)")))
        self.assertTrue(prep.disjoint(Point(-5, -5)))
        poly = Polygon(((-1, -1), (1, 1), (1, 0), (-1, -1)))
        self.assertTrue(prep.overlaps(poly))
        poly = Polygon(((-5, 0), (-5, 5), (0, 5), (-5, 0)))
        self.assertTrue(prep.touches(poly))
        poly = Polygon(((-1, -1), (-1, 11), (11, 11), (11, -1), (-1, -1)))
        self.assertTrue(prep.within(poly))

        # Original geometry deletion should not crash the prepared one (#21662)
        del mpoly
        self.assertTrue(prep.covers(Point(5, 5)))