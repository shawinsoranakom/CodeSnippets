def test_extent(self):
        "Testing `extent` method."
        # The xmin, ymin, xmax, ymax of the MultiPoint should be returned.
        mp = MultiPoint(Point(5, 23), Point(0, 0), Point(10, 50))
        self.assertEqual((0.0, 0.0, 10.0, 50.0), mp.extent)
        pnt = Point(5.23, 17.8)
        # Extent of points is just the point itself repeated.
        self.assertEqual((5.23, 17.8, 5.23, 17.8), pnt.extent)
        # Testing on the 'real world' Polygon.
        poly = fromstr(self.geometries.polygons[3].wkt)
        ring = poly.shell
        x, y = ring.x, ring.y
        xmin, ymin = min(x), min(y)
        xmax, ymax = max(x), max(y)
        self.assertEqual((xmin, ymin, xmax, ymax), poly.extent)