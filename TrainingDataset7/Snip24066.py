def test_centroid(self):
        point = OGRGeometry("POINT (1 2 3)")
        self.assertEqual(point.centroid.wkt, "POINT (1 2)")
        linestring = OGRGeometry("LINESTRING (0 0 0, 1 1 1, 2 2 2)")
        self.assertEqual(linestring.centroid.wkt, "POINT (1 1)")
        polygon = OGRGeometry("POLYGON((0 0, 10 0, 10 10, 0 10, 0 0))")
        self.assertEqual(polygon.centroid.wkt, "POINT (5 5)")
        multipoint = OGRGeometry("MULTIPOINT (0 0,10 10)")
        self.assertEqual(multipoint.centroid.wkt, "POINT (5 5)")
        multilinestring = OGRGeometry(
            "MULTILINESTRING ((0 0,0 10,0 20),(10 0,10 10,10 20))"
        )
        self.assertEqual(multilinestring.centroid.wkt, "POINT (5 10)")
        multipolygon = OGRGeometry(
            "MULTIPOLYGON(((0 0, 10 0, 10 10, 0 10, 0 0)),"
            "((20 20, 20 30, 30 30, 30 20, 20 20)))"
        )
        self.assertEqual(multipolygon.centroid.wkt, "POINT (15 15)")
        geometrycollection = OGRGeometry(
            "GEOMETRYCOLLECTION (POINT (110 260),LINESTRING (110 0,110 60))"
        )
        self.assertEqual(geometrycollection.centroid.wkt, "POINT (110 30)")