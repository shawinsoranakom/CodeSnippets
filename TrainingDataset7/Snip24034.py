def test_srs_transform(self):
        "Testing transform()."
        orig = OGRGeometry("POINT (-104.609 38.255)", 4326)
        trans = OGRGeometry("POINT (992385.4472045 481455.4944650)", 2774)

        # Using an srid, a SpatialReference object, and a CoordTransform object
        # or transformations.
        t1, t2, t3 = orig.clone(), orig.clone(), orig.clone()
        t1.transform(trans.srid)
        t2.transform(SpatialReference("EPSG:2774"))
        ct = CoordTransform(SpatialReference("WGS84"), SpatialReference(2774))
        t3.transform(ct)

        # Testing use of the `clone` keyword.
        k1 = orig.clone()
        k2 = k1.transform(trans.srid, clone=True)
        self.assertEqual(k1, orig)
        self.assertNotEqual(k1, k2)

        # Different PROJ versions use different transformations, all are
        # correct as having a 1 meter accuracy.
        prec = -1
        for p in (t1, t2, t3, k2):
            self.assertAlmostEqual(trans.x, p.x, prec)
            self.assertAlmostEqual(trans.y, p.y, prec)