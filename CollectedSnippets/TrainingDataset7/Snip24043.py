def test_pickle(self):
        "Testing pickle support."
        g1 = OGRGeometry("LINESTRING(1 1 1,2 2 2,3 3 3)", "WGS84")
        g2 = pickle.loads(pickle.dumps(g1))
        self.assertEqual(g1, g2)
        self.assertEqual(4326, g2.srs.srid)
        self.assertEqual(g1.srs.wkt, g2.srs.wkt)