def test_extent(self):
        "Testing `extent` property."
        # The xmin, ymin, xmax, ymax of the MultiPoint should be returned.
        mp = OGRGeometry("MULTIPOINT(5 23, 0 0, 10 50)")
        self.assertEqual((0.0, 0.0, 10.0, 50.0), mp.extent)
        # Testing on the 'real world' Polygon.
        poly = OGRGeometry(self.geometries.polygons[3].wkt)
        ring = poly.shell
        x, y = ring.x, ring.y
        xmin, ymin = min(x), min(y)
        xmax, ymax = max(x), max(y)
        self.assertEqual((xmin, ymin, xmax, ymax), poly.extent)