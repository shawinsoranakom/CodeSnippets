def test_intersects(self):
        self.assertIs(
            OGRGeometry("LINESTRING(0 0, 1 1)").intersects(
                OGRGeometry("LINESTRING(0 1, 1 0)")
            ),
            True,
        )
        self.assertIs(
            OGRGeometry("LINESTRING(0 0, 0 1)").intersects(
                OGRGeometry("LINESTRING(1 0, 1 1)")
            ),
            False,
        )