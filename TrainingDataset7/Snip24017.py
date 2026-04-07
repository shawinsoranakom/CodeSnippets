def test_geomtype_25d(self):
        "Testing OGRGeomType object with 25D types."
        wkb25bit = OGRGeomType.wkb25bit
        self.assertEqual(OGRGeomType(wkb25bit + 1), "Point25D")
        self.assertEqual(OGRGeomType("MultiLineString25D"), (5 + wkb25bit))
        self.assertEqual(
            "GeometryCollectionField", OGRGeomType("GeometryCollection25D").django
        )