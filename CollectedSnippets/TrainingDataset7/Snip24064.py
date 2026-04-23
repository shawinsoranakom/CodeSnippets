def test_point_m_dimension_types(self):
        geom = OGRGeometry("POINT ZM (1 2 3 4)")
        self.assertEqual(geom.geom_type.name, "PointZM")
        self.assertEqual(geom.geom_type.num, 3001)
        geom = OGRGeometry("POINT M (1 2 3)")
        self.assertEqual(geom.geom_type.name, "PointM")
        self.assertEqual(geom.geom_type.num, 2001)