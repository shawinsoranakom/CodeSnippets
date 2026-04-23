def test_gdal(self):
        "Testing `ogr` and `srs` properties."
        g1 = fromstr("POINT(5 23)")
        self.assertIsInstance(g1.ogr, gdal.OGRGeometry)
        self.assertIsNone(g1.srs)

        g1_3d = fromstr("POINT(5 23 8)")
        self.assertIsInstance(g1_3d.ogr, gdal.OGRGeometry)
        self.assertEqual(g1_3d.ogr.z, 8)

        g2 = fromstr("LINESTRING(0 0, 5 5, 23 23)", srid=4326)
        self.assertIsInstance(g2.ogr, gdal.OGRGeometry)
        self.assertIsInstance(g2.srs, gdal.SpatialReference)
        self.assertEqual(g2.hex, g2.ogr.hex)
        self.assertEqual("WGS 84", g2.srs.name)