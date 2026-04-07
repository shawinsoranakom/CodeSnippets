def test_valid_reason(self):
        "Testing IsValidReason support"

        g = GEOSGeometry("POINT(0 0)")
        self.assertTrue(g.valid)
        self.assertIsInstance(g.valid_reason, str)
        self.assertEqual(g.valid_reason, "Valid Geometry")

        g = GEOSGeometry("LINESTRING(0 0, 0 0)")

        self.assertFalse(g.valid)
        self.assertIsInstance(g.valid_reason, str)
        self.assertTrue(
            g.valid_reason.startswith("Too few points in geometry component")
        )