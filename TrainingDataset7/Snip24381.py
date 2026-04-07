def test_transform(self):
        "Testing `transform` method."
        orig = GEOSGeometry("POINT (-104.609 38.255)", 4326)
        trans = GEOSGeometry("POINT (992385.4472045 481455.4944650)", 2774)

        # Using a srid, a SpatialReference object, and a CoordTransform object
        # for transformations.
        t1, t2, t3 = orig.clone(), orig.clone(), orig.clone()
        t1.transform(trans.srid)
        t2.transform(gdal.SpatialReference("EPSG:2774"))
        ct = gdal.CoordTransform(
            gdal.SpatialReference("WGS84"), gdal.SpatialReference(2774)
        )
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
            with self.subTest(p=p):
                self.assertAlmostEqual(trans.x, p.x, prec)
                self.assertAlmostEqual(trans.y, p.y, prec)