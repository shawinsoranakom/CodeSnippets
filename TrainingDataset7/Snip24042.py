def test_25D(self):
        "Testing 2.5D geometries."
        pnt_25d = OGRGeometry("POINT(1 2 3)")
        self.assertEqual("Point25D", pnt_25d.geom_type.name)
        self.assertEqual(3.0, pnt_25d.z)
        self.assertEqual(3, pnt_25d.coord_dim)
        ls_25d = OGRGeometry("LINESTRING(1 1 1,2 2 2,3 3 3)")
        self.assertEqual("LineString25D", ls_25d.geom_type.name)
        self.assertEqual([1.0, 2.0, 3.0], ls_25d.z)
        self.assertEqual(3, ls_25d.coord_dim)