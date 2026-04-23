def test_wkb(self):
        "Testing WKB input/output."
        for g in self.geometries.hex_wkt:
            geom1 = OGRGeometry(g.wkt)
            wkb = geom1.wkb
            self.assertEqual(wkb.hex().upper(), g.hex)
            # Constructing w/WKB.
            geom2 = OGRGeometry(wkb)
            self.assertEqual(geom1, geom2)