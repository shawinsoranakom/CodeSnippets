def test_closepolygons(self):
        "Testing closing Polygon objects."
        # Both rings in this geometry are not closed.
        poly = OGRGeometry("POLYGON((0 0, 5 0, 5 5, 0 5), (1 1, 2 1, 2 2, 2 1))")
        self.assertEqual(8, poly.point_count)
        with self.assertRaises(GDALException):
            poly.centroid

        poly.close_rings()
        self.assertEqual(
            10, poly.point_count
        )  # Two closing points should've been added
        self.assertEqual(OGRGeometry("POINT(2.5 2.5)"), poly.centroid)