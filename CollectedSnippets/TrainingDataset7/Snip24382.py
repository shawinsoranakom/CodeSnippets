def test_transform_3d(self):
        p3d = GEOSGeometry("POINT (5 23 100)", 4326)
        p3d.transform(2774)
        self.assertAlmostEqual(p3d.z, 100, 3)