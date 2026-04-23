def test_distance(self):
        "Testing the distance() function."
        # Distance to self should be 0.
        pnt = Point(0, 0)
        self.assertEqual(0.0, pnt.distance(Point(0, 0)))

        # Distance should be 1
        self.assertEqual(1.0, pnt.distance(Point(0, 1)))

        # Distance should be ~ sqrt(2)
        self.assertAlmostEqual(1.41421356237, pnt.distance(Point(1, 1)), 11)

        # Distances are from the closest vertex in each geometry --
        #  should be 3 (distance from (2, 2) to (5, 2)).
        ls1 = LineString((0, 0), (1, 1), (2, 2))
        ls2 = LineString((5, 2), (6, 1), (7, 0))
        self.assertEqual(3, ls1.distance(ls2))