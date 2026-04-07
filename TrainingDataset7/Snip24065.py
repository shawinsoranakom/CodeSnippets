def test_point_m_dimension_geos(self):
        """GEOSGeometry does not yet support the M dimension."""
        geom = OGRGeometry("POINT ZM (1 2 3 4)")
        self.assertEqual(geom.geos.wkt, "POINT Z (1 2 3)")
        geom = OGRGeometry("POINT M (1 2 3)")
        self.assertEqual(geom.geos.wkt, "POINT (1 2)")