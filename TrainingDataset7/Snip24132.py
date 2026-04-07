def test_axis_order(self):
        wgs84_trad = SpatialReference(4326, axis_order=AxisOrder.TRADITIONAL)
        wgs84_auth = SpatialReference(4326, axis_order=AxisOrder.AUTHORITY)
        # Coordinate interpretation may depend on the srs axis predicate.
        pt = GEOSGeometry("POINT (992385.4472045 481455.4944650)", 2774)
        pt_trad = pt.transform(wgs84_trad, clone=True)
        self.assertAlmostEqual(pt_trad.x, -104.609, 3)
        self.assertAlmostEqual(pt_trad.y, 38.255, 3)
        pt_auth = pt.transform(wgs84_auth, clone=True)
        self.assertAlmostEqual(pt_auth.x, 38.255, 3)
        self.assertAlmostEqual(pt_auth.y, -104.609, 3)
        # clone() preserves the axis order.
        pt_auth = pt.transform(wgs84_auth.clone(), clone=True)
        self.assertAlmostEqual(pt_auth.x, 38.255, 3)
        self.assertAlmostEqual(pt_auth.y, -104.609, 3)