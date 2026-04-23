def test_transform_noop(self):
        """Testing `transform` method (SRID match)"""
        # transform() should no-op if source & dest SRIDs match,
        # regardless of whether GDAL is available.
        g = GEOSGeometry("POINT (-104.609 38.255)", 4326)
        gt = g.tuple
        g.transform(4326)
        self.assertEqual(g.tuple, gt)
        self.assertEqual(g.srid, 4326)

        g = GEOSGeometry("POINT (-104.609 38.255)", 4326)
        g1 = g.transform(4326, clone=True)
        self.assertEqual(g1.tuple, g.tuple)
        self.assertEqual(g1.srid, 4326)
        self.assertIsNot(g1, g, "Clone didn't happen")