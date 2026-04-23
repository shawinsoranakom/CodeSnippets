def test_wkt(self):
        "Testing WKT output."
        for g in self.geometries.wkt_out:
            geom = OGRGeometry(g.wkt)
            self.assertEqual(g.wkt, geom.wkt)