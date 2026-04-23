def test07_boolean_props(self):
        "Testing the boolean properties."
        for s in srlist:
            srs = SpatialReference(s.wkt)
            self.assertEqual(s.projected, srs.projected)
            self.assertEqual(s.geographic, srs.geographic)