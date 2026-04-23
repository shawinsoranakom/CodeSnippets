def test_ewkt(self):
        "Testing EWKT input/output."
        for ewkt_val in ("POINT (1 2 3)", "LINEARRING (0 0,1 1,2 1,0 0)"):
            # First with ewkt output when no SRID in EWKT
            self.assertEqual(ewkt_val, OGRGeometry(ewkt_val).ewkt)
            # No test consumption with an SRID specified.
            ewkt_val = "SRID=4326;%s" % ewkt_val
            geom = OGRGeometry(ewkt_val)
            self.assertEqual(ewkt_val, geom.ewkt)
            self.assertEqual(4326, geom.srs.srid)