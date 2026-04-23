def test_geom_type_repr(self):
        self.assertEqual(repr(OGRGeomType("point")), "<OGRGeomType: Point>")