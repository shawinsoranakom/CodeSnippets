def test10_attributes(self):
        "Testing the attribute retrieval routines."
        for s in srlist:
            srs = SpatialReference(s.wkt)
            for tup in s.attr:
                att = tup[0]  # Attribute to test
                exp = tup[1]  # Expected result
                self.assertEqual(exp, srs[att])