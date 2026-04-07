def test_wkb(self):
        "Testing WKB output."
        for g in self.geometries.hex_wkt:
            geom = fromstr(g.wkt)
            wkb = geom.wkb
            self.assertEqual(wkb.hex().upper(), g.hex)