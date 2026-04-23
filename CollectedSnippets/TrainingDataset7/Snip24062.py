def test_point_m_tuple(self):
        geom = OGRGeometry("POINT ZM (1 2 3 4)")
        self.assertEqual(geom.tuple, (geom.x, geom.y, geom.z, geom.m))
        geom = OGRGeometry("POINT M (1 2 3)")
        self.assertEqual(geom.tuple, (geom.x, geom.y, geom.m))
        geom = OGRGeometry("POINT Z (1 2 3)")
        self.assertEqual(geom.tuple, (geom.x, geom.y, geom.z))
        geom = OGRGeometry("POINT (1 2 3)")
        self.assertEqual(geom.tuple, (geom.x, geom.y, geom.z))