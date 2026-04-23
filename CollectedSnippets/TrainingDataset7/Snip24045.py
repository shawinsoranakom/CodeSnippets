def test_equivalence_regression(self):
        "Testing equivalence methods with non-OGRGeometry instances."
        self.assertIsNotNone(OGRGeometry("POINT(0 0)"))
        self.assertNotEqual(OGRGeometry("LINESTRING(0 0, 1 1)"), 3)