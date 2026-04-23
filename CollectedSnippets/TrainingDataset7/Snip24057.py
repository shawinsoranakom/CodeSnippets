def test_geometry_types(self):
        tests = [
            ("Point", 1, True),
            ("LineString", 2, True),
            ("Polygon", 3, True),
            ("MultiPoint", 4, True),
            ("Multilinestring", 5, True),
            ("MultiPolygon", 6, True),
            ("GeometryCollection", 7, True),
            ("CircularString", 8, True),
            ("CompoundCurve", 9, True),
            ("CurvePolygon", 10, True),
            ("MultiCurve", 11, True),
            ("MultiSurface", 12, True),
            # 13 (Curve) and 14 (Surface) are abstract types.
            ("PolyhedralSurface", 15, False),
            ("TIN", 16, False),
            ("Triangle", 17, False),
            ("Linearring", 2, True),
            # Types 1 - 7 with Z dimension have 2.5D enums.
            ("Point Z", -2147483647, True),  # 1001
            ("LineString Z", -2147483646, True),  # 1002
            ("Polygon Z", -2147483645, True),  # 1003
            ("MultiPoint Z", -2147483644, True),  # 1004
            ("Multilinestring Z", -2147483643, True),  # 1005
            ("MultiPolygon Z", -2147483642, True),  # 1006
            ("GeometryCollection Z", -2147483641, True),  # 1007
            ("CircularString Z", 1008, True),
            ("CompoundCurve Z", 1009, True),
            ("CurvePolygon Z", 1010, True),
            ("MultiCurve Z", 1011, True),
            ("MultiSurface Z", 1012, True),
            ("PolyhedralSurface Z", 1015, False),
            ("TIN Z", 1016, False),
            ("Triangle Z", 1017, False),
            ("Point M", 2001, True),
            ("LineString M", 2002, True),
            ("Polygon M", 2003, True),
            ("MultiPoint M", 2004, True),
            ("MultiLineString M", 2005, True),
            ("MultiPolygon M", 2006, True),
            ("GeometryCollection M", 2007, True),
            ("CircularString M", 2008, True),
            ("CompoundCurve M", 2009, True),
            ("CurvePolygon M", 2010, True),
            ("MultiCurve M", 2011, True),
            ("MultiSurface M", 2012, True),
            ("PolyhedralSurface M", 2015, False),
            ("TIN M", 2016, False),
            ("Triangle M", 2017, False),
            ("Point ZM", 3001, True),
            ("LineString ZM", 3002, True),
            ("Polygon ZM", 3003, True),
            ("MultiPoint ZM", 3004, True),
            ("MultiLineString ZM", 3005, True),
            ("MultiPolygon ZM", 3006, True),
            ("GeometryCollection ZM", 3007, True),
            ("CircularString ZM", 3008, True),
            ("CompoundCurve ZM", 3009, True),
            ("CurvePolygon ZM", 3010, True),
            ("MultiCurve ZM", 3011, True),
            ("MultiSurface ZM", 3012, True),
            ("PolyhedralSurface ZM", 3015, False),
            ("TIN ZM", 3016, False),
            ("Triangle ZM", 3017, False),
        ]

        for test in tests:
            geom_type, num, supported = test
            with self.subTest(geom_type=geom_type, num=num, supported=supported):
                if supported:
                    g = OGRGeometry(f"{geom_type} EMPTY")
                    self.assertEqual(g.geom_type.num, num)
                else:
                    type_ = geom_type.replace(" ", "")
                    msg = f"Unsupported geometry type: {type_}"
                    with self.assertRaisesMessage(TypeError, msg):
                        OGRGeometry(f"{geom_type} EMPTY")