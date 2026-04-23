def test_equals_identical_geos_version(self):
        g1 = fromstr("POINT (1 2 3)")
        g2 = fromstr("POINT (1 2 3)")
        msg = "GEOSGeometry.equals_identical() requires GEOS >= 3.12.0"
        with self.assertRaisesMessage(GEOSException, msg):
            g1.equals_identical(g2)