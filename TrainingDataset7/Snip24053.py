def test_within(self):
        self.assertIs(
            OGRGeometry("POINT(0.5 0.5)").within(
                OGRGeometry("POLYGON ((0 0, 0 1, 1 1, 1 0, 0 0))")
            ),
            True,
        )
        self.assertIs(
            OGRGeometry("POINT(0 0)").within(OGRGeometry("POINT(0 1)")), False
        )