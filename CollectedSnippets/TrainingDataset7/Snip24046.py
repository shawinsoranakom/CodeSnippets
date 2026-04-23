def test_contains(self):
        self.assertIs(
            OGRGeometry("POINT(0 0)").contains(OGRGeometry("POINT(0 0)")), True
        )
        self.assertIs(
            OGRGeometry("POINT(0 0)").contains(OGRGeometry("POINT(0 1)")), False
        )