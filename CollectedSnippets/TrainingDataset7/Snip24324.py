def test_create_wkb(self):
        "Testing creation from WKB."
        for g in self.geometries.hex_wkt:
            wkb = memoryview(bytes.fromhex(g.hex))
            geom_h = GEOSGeometry(wkb)
            # we need to do this so decimal places get normalized
            geom_t = fromstr(g.wkt)
            with self.subTest(g=g):
                self.assertEqual(geom_t.wkt, geom_h.wkt)