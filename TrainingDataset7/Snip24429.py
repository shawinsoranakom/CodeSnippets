def test_wktwriter_constructor_arguments(self):
        wkt_w = WKTWriter(dim=3, trim=True, precision=3)
        ref = GEOSGeometry("POINT (5.34562 23 1.5)")
        ref_wkt = "POINT Z (5.346 23 1.5)"
        self.assertEqual(ref_wkt, wkt_w.write(ref).decode())