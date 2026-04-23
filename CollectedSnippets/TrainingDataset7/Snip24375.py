def test_length(self):
        "Testing the length property."
        # Points have 0 length.
        pnt = Point(0, 0)
        self.assertEqual(0.0, pnt.length)

        # Should be ~ sqrt(2)
        ls = LineString((0, 0), (1, 1))
        self.assertAlmostEqual(1.41421356237, ls.length, 11)

        # Should be circumference of Polygon
        poly = Polygon(LinearRing((0, 0), (0, 1), (1, 1), (1, 0), (0, 0)))
        self.assertEqual(4.0, poly.length)

        # Should be sum of each element's length in collection.
        mpoly = MultiPolygon(poly.clone(), poly)
        self.assertEqual(8.0, mpoly.length)