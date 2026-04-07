def test_wkt(self):
        "Testing WKT output."
        for g in self.geometries.wkt_out:
            with self.subTest(g=g):
                geom = fromstr(g.wkt)
                if geom.hasz:
                    self.assertEqual(g.ewkt, geom.wkt)