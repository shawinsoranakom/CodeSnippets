def test_hasm_geos_version(self):
        p = fromstr("POINT (1 2 3)")
        msg = "GEOSGeometry.hasm requires GEOS >= 3.12.0."
        with self.assertRaisesMessage(GEOSException, msg):
            p.hasm