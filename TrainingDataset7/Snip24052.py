def test_touches(self):
        self.assertIs(
            OGRGeometry("POLYGON ((0 0, 0 1, 1 1, 1 0, 0 0))").touches(
                OGRGeometry("LINESTRING(0 2, 2 0)")
            ),
            True,
        )
        self.assertIs(
            OGRGeometry("POINT(0 0)").touches(OGRGeometry("POINT(0 1)")), False
        )