def test_create_hex(self):
        "Testing creation from HEX."
        for g in self.geometries.hex_wkt:
            geom_h = GEOSGeometry(g.hex)
            # we need to do this so decimal places get normalized
            geom_t = fromstr(g.wkt)
            with self.subTest(g=g):
                self.assertEqual(geom_t.wkt, geom_h.wkt)