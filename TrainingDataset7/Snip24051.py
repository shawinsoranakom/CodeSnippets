def test_overlaps(self):
        self.assertIs(
            OGRGeometry("POLYGON ((0 0, 0 2, 2 2, 2 0, 0 0))").overlaps(
                OGRGeometry("POLYGON ((1 1, 1 5, 5 5, 5 1, 1 1))")
            ),
            True,
        )
        self.assertIs(
            OGRGeometry("POINT(0 0)").overlaps(OGRGeometry("POINT(0 1)")), False
        )