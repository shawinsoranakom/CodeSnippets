def test_disjoint(self):
        self.assertIs(
            OGRGeometry("LINESTRING(0 0, 1 1)").disjoint(
                OGRGeometry("LINESTRING(0 1, 1 0)")
            ),
            False,
        )
        self.assertIs(
            OGRGeometry("LINESTRING(0 0, 0 1)").disjoint(
                OGRGeometry("LINESTRING(1 0, 1 1)")
            ),
            True,
        )