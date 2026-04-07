def test_multi_geometries_m_dimension(self):
        tests = [
            "MULTIPOINT M ((10 40 10), (40 30 10), (20 20 10))",
            "MULTIPOINT ZM ((10 40 0 10), (40 30 1 10), (20 20 1 10))",
            "MULTILINESTRING M ((10 10 1, 20 20 2),(40 40 1, 30 30 2))",
            "MULTILINESTRING ZM ((10 10 0 1, 20 20 0 2),(40 40 1, 30 30 0 2))",
            (
                "MULTIPOLYGON ZM (((30 20 1 0, 45 40 1 0, 30 20 1 0)),"
                "((15 5 0 0, 40 10 0 0, 15 5 0 0)))"
            ),
            (
                "GEOMETRYCOLLECTION M (POINT M (40 10 0),"
                "LINESTRING M (10 10 0, 20 20 0, 10 40 0))"
            ),
            (
                "GEOMETRYCOLLECTION ZM (POINT ZM (40 10 0 1),"
                "LINESTRING ZM (10 10 1 0, 20 20 1 0, 10 40 1 0))"
            ),
        ]
        for geom_input in tests:
            with self.subTest(geom_input=geom_input):
                geom = OGRGeometry(geom_input)
                self.assertIs(geom.is_measured, True)