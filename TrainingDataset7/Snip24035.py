def test_transform_dim(self):
        "Testing coordinate dimension is the same on transformed geometries."
        ls_orig = OGRGeometry("LINESTRING(-104.609 38.255)", 4326)
        ls_trans = OGRGeometry("LINESTRING(992385.4472045 481455.4944650)", 2774)

        # Different PROJ versions use different transformations, all are
        # correct as having a 1 meter accuracy.
        prec = -1
        ls_orig.transform(ls_trans.srs)
        # Making sure the coordinate dimension is still 2D.
        self.assertEqual(2, ls_orig.coord_dim)
        self.assertAlmostEqual(ls_trans.x[0], ls_orig.x[0], prec)
        self.assertAlmostEqual(ls_trans.y[0], ls_orig.y[0], prec)