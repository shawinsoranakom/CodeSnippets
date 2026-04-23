def test_ewkt(self):
        "Testing EWKT."
        srids = (-1, 32140)
        for srid in srids:
            for p in self.geometries.polygons:
                ewkt = "SRID=%d;%s" % (srid, p.wkt)
                poly = fromstr(ewkt)
                with self.subTest(p=p):
                    self.assertEqual(srid, poly.srid)
                    self.assertEqual(srid, poly.shell.srid)
                    self.assertEqual(srid, fromstr(poly.ewkt).srid)