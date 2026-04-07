def test_crosses(self):
        self.assertIs(
            OGRGeometry("LINESTRING(0 0, 1 1)").crosses(
                OGRGeometry("LINESTRING(0 1, 1 0)")
            ),
            True,
        )
        self.assertIs(
            OGRGeometry("LINESTRING(0 0, 0 1)").crosses(
                OGRGeometry("LINESTRING(1 0, 1 1)")
            ),
            False,
        )