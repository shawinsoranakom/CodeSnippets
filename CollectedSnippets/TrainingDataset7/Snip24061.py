def test_point_m_coordinate(self):
        geom = OGRGeometry("POINT ZM (1 2 3 4)")
        self.assertEqual(geom.m, 4)
        geom = OGRGeometry("POINT (1 2 3 4)")
        self.assertEqual(geom.m, 4)
        geom = OGRGeometry("POINT M (1 2 3)")
        self.assertEqual(geom.m, 3)
        geom = OGRGeometry("POINT Z (1 2 3)")
        self.assertEqual(geom.m, None)