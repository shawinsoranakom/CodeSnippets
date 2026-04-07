def test_geomtype(self):
        "Testing OGRGeomType object."

        # OGRGeomType should initialize on all these inputs.
        OGRGeomType(1)
        OGRGeomType(7)
        OGRGeomType("point")
        OGRGeomType("GeometrycollectioN")
        OGRGeomType("LINearrING")
        OGRGeomType("Unknown")

        # Should throw TypeError on this input
        with self.assertRaises(GDALException):
            OGRGeomType(23)
        with self.assertRaises(GDALException):
            OGRGeomType("fooD")
        with self.assertRaises(GDALException):
            OGRGeomType(4001)

        # Equivalence can take strings, ints, and other OGRGeomTypes
        self.assertEqual(OGRGeomType(1), OGRGeomType(1))
        self.assertEqual(OGRGeomType(7), "GeometryCollection")
        self.assertEqual(OGRGeomType("point"), "POINT")
        self.assertNotEqual(OGRGeomType("point"), 2)
        self.assertEqual(OGRGeomType("unknown"), 0)
        self.assertEqual(OGRGeomType(6), "MULtiPolyGON")
        self.assertEqual(OGRGeomType(1), OGRGeomType("point"))
        self.assertNotEqual(OGRGeomType("POINT"), OGRGeomType(6))

        # Testing the Django field name equivalent property.
        self.assertEqual("PointField", OGRGeomType("Point").django)
        self.assertEqual("GeometryField", OGRGeomType("Geometry").django)
        self.assertEqual("GeometryField", OGRGeomType("Unknown").django)
        self.assertIsNone(OGRGeomType("none").django)

        # 'Geometry' initialization implies an unknown geometry type.
        gt = OGRGeomType("Geometry")
        self.assertEqual(0, gt.num)
        self.assertEqual("Unknown", gt.name)